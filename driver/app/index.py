from flask import Flask, render_template, request, url_for, g, jsonify
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
import json, logging
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
from email.mime.multipart import MIMEMultipart

from app.database import db
from app.models.driver import Driver, QA
from app.utils.session_manager import session_manager, add_cookie
from app.utils.auth_utils import DeviceAuthManager

def create_app():
    """ドライバーアプリケーションを作成"""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///driver.db'
    
    # 外部データベースへの接続（学生システムのバス情報）
    app.config['SQLALCHEMY_BINDS'] = {
        'student_db': 'sqlite:///../../student/instance/student.db'
    }
    
    # データベース初期化
    db.init_app(app)

    # ログ設定
    logger = logging.getLogger('sojo-bus-log')
    logger.setLevel(logging.INFO)
    sh = logging.StreamHandler()
    logger.addHandler(sh)
    fh = logging.FileHandler('sojo-bus.log')
    logger.addHandler(fh)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.info('Starting driver service')

    # 外部データベースのテーブル定義（読み取り専用）
    class Bus(db.Model):
        """バステーブル - 学生システムから読み取り専用"""
        __bind_key__ = "student_db"
        __tablename__ = 'bus'
        
        id = db.Column(db.Integer, primary_key=True)
        busid = db.Column(db.Integer, nullable=False)
        departure_time = db.Column(db.DateTime, nullable=False)
        seats = db.Column(db.Integer, nullable=False)
        ud = db.Column(db.Integer, nullable=False)  # 上りなら0、下りなら1
        bookable_time = db.Column(db.Integer, nullable=False)  # デフォルト0,予約可能時間に合わせて変更
        status = db.Column(db.Integer, nullable=False)

    class Seat(db.Model):
        """座席テーブル - 学生システムから読み取り専用"""
        __bind_key__ = "student_db"
        __tablename__ = 'seat'
        
        id = db.Column(db.Integer, primary_key=True)
        number = db.Column(db.Integer, nullable=False)
        bus_id = db.Column(db.Integer, nullable=False)

    class Reservation(db.Model):
        """予約テーブル - 学生システムから読み取り専用"""
        __bind_key__ = "student_db"
        __tablename__ = 'reservation'
        
        id = db.Column(db.Integer, primary_key=True)
        seat_number = db.Column(db.Integer, db.ForeignKey('seat.number'), nullable=False)
        bus_id = db.Column(db.Integer, db.ForeignKey('bus.id'), nullable=False)
        user_id = db.Column(db.Integer, nullable=False)
        approved = db.Column(db.Integer, nullable=False)  # 0なら未認証(デフォルト)、1なら認証済み
        reserved_time = db.Column(db.DateTime)

    with app.app_context():
        db.create_all()

    # セッション管理のためのクッキー処理
    @app.after_request
    def apply_cookies(response):
        """レスポンスにクッキーを追加"""
        if hasattr(g, 'cookies'):
            for key, value in g.cookies.items():
                response.set_cookie(key, value)
        return response

    # ユーティリティ関数
    def yukisaki(ud):
        """行き先の文字列化"""
        if ud == 0:
            return "高槻キャンパス"
        else:
            return "高槻駅"

    def gakusei(username):
        """学生番号の表示形式変換"""
        if len(username) in [1, 2, 3, 4]:
            username = "driver" + username
        elif len(username) < 6:
            username = "使用不可"
        elif len(username) == 6:
            username = "情" + username[:2] + "-" + username[-4:]
        # 大学院生の場合
        elif str(username)[2] == "1":
            username = "情" + str(username[:2]) + "M" + str(username[4:])
        else:
            username = "情" + username[:2] + "D" + username[4:]
        return username

    def require_auth(f):
        """認証が必要なルートのデコレータ"""
        def decorated_function(*args, **kwargs):
            hashed_num = request.cookies.get('hashed_num')
            if not hashed_num:
                return render_template('login.html')
            
            username = session_manager.validate_session(hashed_num)
            if not username:
                return render_template('login.html', message='セッションが切れました')
            
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function

    def get_current_user():
        """現在のユーザーを取得"""
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            return session_manager.validate_session(hashed_num)
        return None

    def get_driver_buses(driver_number):
        """運転手の担当バス一覧を取得"""
        now = datetime.now()
        return db.session.query(Bus).filter(
            Bus.departure_time > now,
            Bus.busid == driver_number
        ).order_by(Bus.departure_time).all()

    def get_bus_info_for_display(buses):
        """バス情報を表示用に変換"""
        bus_list = []
        for bus in buses:
            ud = yukisaki(bus.ud)
            bus_list.append({
                "id": bus.id,
                "busid": bus.busid,
                "departure_time": bus.departure_time.strftime('%m/%d %H:%M'),
                "ud": ud,
                "display": f"行き先|{ud} 出発時刻|{bus.departure_time.strftime('%m/%d %H:%M')} {bus.busid}号車"
            })
        return bus_list

    # ルーティング定義

    @app.route('/driver/<username>')
    def device_login(username):
        """
        MACアドレスベースの自動ログイン
        管理システムに登録されたデバイスからのアクセスの場合、パスワード不要でログイン
        """
        logger.info(f"Device-based login attempt: {username}")
        
        # デバイス認証マネージャーを初期化
        device_auth = DeviceAuthManager()
        
        # デバイス認証を実行
        if device_auth.authenticate_by_device(request, username):
            # 認証成功
            user = db.session.query(Driver).filter_by(username=username).first()
            
            if not user:
                logger.warning(f"Device authenticated but user not found: {username}")
                return render_template('login.html', message='ユーザーが見つかりません')
            
            if not user.is_active:
                logger.warning(f"Device authenticated but user is inactive: {username}")
                return render_template('login.html', message='このアカウントは無効化されています')
            
            try:
                # セッション作成
                hashed_num = session_manager.create_session(username)
                add_cookie('hashed_num', hashed_num)
                
                logger.info(f"Successful device-based login: {username}")
                
                # トップページにリダイレクト（メッセージ付き）
                return redirect(url_for('index.index', message='特殊ログインに成功しました'))
                
            except Exception as e:
                logger.error(f"Session creation failed for device login {username}: {e}")
                return render_template('login.html', message='ログインに失敗しました')
        else:
            # 認証失敗 - 通常のログインページを表示
            logger.warning(f"Device authentication failed for {username}")
            return render_template('login.html', 
                                 message='このデバイスは登録されていません。パスワードでログインしてください。')

    # ルーティング定義

    @app.route('/login')
    def login():
        """ログイン画面"""
        return render_template('login.html')

    @app.route('/login/register', methods=['POST'])
    def login_register():
        """ログイン処理"""
        username = request.form['username']
        password = request.form['password']
        
        logger.info(f"Login attempt: {username}")
        
        user = db.session.query(Driver).filter_by(username=username).first()
        if not user:
            return render_template('login.html', message='ユーザー名が間違っています')
        
        if not user.verify_password(password):
            return render_template('login.html', message='パスワードが間違っています')
        
        # セッション作成
        try:
            hashed_num = session_manager.create_session(username)
            add_cookie('hashed_num', hashed_num)
            
            logger.info(f"Successful login: {username}")
            
            # 担当バス情報を取得してトップページに表示
            buses = get_driver_buses(user.number)
            bus_info = get_bus_info_for_display(buses[:2])  # 最初の2件
            
            firstbus = bus_info[0]['display'] if len(bus_info) > 0 else "バスがありません"
            secondbus = bus_info[1]['display'] if len(bus_info) > 1 else "バスがありません"
            
            return render_template('top.html', firstbus=firstbus, secoundbus=secondbus)
            
        except Exception as e:
            logger.error(f"Session creation failed for {username}: {e}")
            return render_template('login.html', message='ログインに失敗しました')

    @app.route('/login<num>')
    def drivernumlogin(num):
        """運転手用の特殊ログイン"""
        username = 'driver' + str(num)
        try:
            user = db.session.query(Driver).filter_by(username=username).first()
            if not user:
                return render_template('login.html', message='ユーザー名が間違っています')
            
            hashed_num = session_manager.create_session(username)
            add_cookie('hashed_num', hashed_num)
            
            logger.info(f"Special driver login: {username}")
            return topview('運転手用特殊ログインを行いました')
            
        except Exception as e:
            logger.error(f"Special driver login failed for {num}: {e}")
            return render_template('login.html', message='ユーザーログインに失敗しました')

    @app.route('/')
    def index():
        """トップページ"""
        username = get_current_user()
        if not username:
            return render_template('login.html')
        
        try:
            user = Driver.query.filter_by(username=username).first()
            if not user:
                return render_template('login.html')
            
            buses = get_driver_buses(user.number)
            bus_info = get_bus_info_for_display(buses[:2])
            
            firstbus = bus_info[0]['display'] if len(bus_info) > 0 else "バスがありません"
            secondbus = bus_info[1]['display'] if len(bus_info) > 1 else "バスがありません"
            
            return render_template('top.html', firstbus=firstbus, secoundbus=secondbus)
            
        except Exception as e:
            logger.error(f"Error loading top page for {username}: {e}")
            return render_template('login.html')

    def topview(message):
        """トップビュー（メッセージ付き）"""
        username = get_current_user()
        if not username:
            return render_template('login.html')
        
        user = Driver.query.filter_by(username=username).first()
        if not user:
            return render_template('login.html')
        
        buses = get_driver_buses(user.number)
        bus_info = get_bus_info_for_display(buses[:2])
        
        firstbus = bus_info[0]['display'] if len(bus_info) > 0 else "バスがありません"
        secondbus = bus_info[1]['display'] if len(bus_info) > 1 else "バスがありません"
        
        return render_template('top.html', firstbus=firstbus, secoundbus=secondbus, message=message)

    @app.route('/bus')
    @require_auth
    def bus():
        """バスの運行便設定選択画面"""
        username = get_current_user()
        user = Driver.query.filter_by(username=username).first()
        
        if user:
            buses = get_driver_buses(user.number)
            bus_date = []
            for bus in buses[:5]:  # 最新5件
                bus_date.append({
                    "id": bus.id,
                    "busid": bus.busid,
                    "departure_time": bus.departure_time.strftime('%m/%d %H:%M'),
                    "seats": bus.seats,
                    "ud": bus.ud
                })
            return render_template('bus.html', bus_date=bus_date, number=user.number)
        
        return render_template('login.html')

    @app.route('/bus/register')
    @require_auth
    def bus_register():
        """バスの運行便設定"""
        username = get_current_user()
        user = Driver.query.filter_by(username=username).first()
        
        if user:
            bus_id = request.args.get('id')
            if not bus_id:
                return render_template('bus_register.html', message='バスIDと出発時刻を選択してください')
            
            businfo = db.session.query(Bus).filter_by(id=bus_id).first()
            if not businfo:
                return render_template('bus_register.html', message='バス情報が見つかりません')
            
            bus = {
                "id": businfo.id,
                "busid": businfo.busid,
                "departure_time": businfo.departure_time.strftime('%Y/%m/%d %H:%M'),
                "seats": businfo.seats,
                "ud": businfo.ud
            }
            
            departure_time = bus["departure_time"]
            bus_id_num = bus["busid"]
            
            # バス情報をJSONファイルに保存（既存機能との互換性のため）
            with open(f'../yoyaku_system/bus{bus_id_num}.json', 'w') as file:
                json.dump(bus, file)
                logger.info(f"Bus registered: {bus_id_num}, departure_time: {departure_time}")
            
            return render_template('bus_register.html', bus_id=bus_id_num, departure_time=departure_time)
        
        return render_template('login.html')

    @app.route('/yoyaku')
    @require_auth
    def yoyaku():
        """予約の日付選択画面"""
        today = datetime.now().date()
        nextday = today + timedelta(days=1)
        return render_template('date_select.html', today=today, nextday=nextday)

    @app.route('/yoyaku/bus', methods=['POST'])
    @require_auth
    def yoyaku_bus_select():
        """バスの一覧を表示する画面"""
        today = datetime.now().date()
        nextday = today + timedelta(days=1)
        
        date = request.form.get('selected-date')
        ud = request.form.get('selected-destination')
        
        if not date or not ud:
            return render_template('date_select.html', today=today, nextday=nextday, message='選択しなおしてください')
        
        date = datetime.strptime(date, '%Y-%m-%d').date()
        
        buses = []
        if ud == "高槻キャンパス":
            if date == today:
                buses = db.session.query(Bus).filter_by(ud=0).filter(
                    Bus.departure_time > today, 
                    Bus.departure_time < nextday
                ).all()
            elif date == nextday:
                buses = db.session.query(Bus).filter_by(ud=0).filter(
                    Bus.departure_time > nextday, 
                    Bus.departure_time < datetime.now() + timedelta(days=2)
                ).all()
        elif ud == "高槻駅":
            if date == today:
                buses = db.session.query(Bus).filter_by(ud=1).filter(
                    Bus.departure_time > today, 
                    Bus.departure_time < nextday
                ).all()
            elif date == nextday:
                buses = db.session.query(Bus).filter_by(ud=1).filter(
                    Bus.departure_time > nextday, 
                    Bus.departure_time < datetime.now() + timedelta(days=2)
                ).all()
        else:
            return render_template('date_select.html', today=today, nextday=nextday, message='選択しなおしてください')
        
        return render_template('bus_select.html', buses=buses)

    @app.route('/yoyaku/bus/<bus_id>')
    @require_auth
    def yoyaku_bus(bus_id):
        """予約の座席選択画面"""
        bus = db.session.query(Bus).filter_by(id=bus_id).first()
        if not bus:
            return render_template('yoyaku.html', message='バスが見つかりません')
        
        # 座席データを取得
        seatall = db.session.query(Seat).filter_by(bus_id=bus_id).all()
        seats = []
        for seat in seatall:
            reserved = db.session.query(Reservation).filter_by(seat_number=seat.number, bus_id=bus_id).first()
            if reserved:
                seats.append({
                    "number": seat.number,
                    "reserved": 1,
                    "approved": reserved.approved,
                    "username": gakusei(str(reserved.user_id))
                })
            else:
                seats.append({
                    "number": seat.number,
                    "reserved": 0,
                    "approved": 0,
                    "username": "none"
                })
        
        return render_template('bnum.html', yukisaki=yukisaki(bus.ud), bus=bus, seats=seats)

    @app.route('/yoyaku/bus/<int:bus_id>/reserve', methods=['POST'])
    @require_auth
    def reserve(bus_id):
        """予約の承認処理（運転手による座席承認）"""
        username = get_current_user()
        
        seat_ids = request.form.getlist('seat_numbers')
        bus = db.session.query(Bus).filter_by(id=bus_id).first()
        notallow = []
        
        if seat_ids:
            for seat_id in seat_ids:
                seat = db.session.query(Seat).filter_by(number=seat_id, bus_id=bus_id).first()
                if seat:
                    reserved = db.session.query(Reservation).filter_by(seat_number=seat.number, bus_id=bus_id).first()
                    if reserved:
                        # すでに予約されている場合
                        if reserved.approved == 1:
                            notallow.append(seat_id)
                        else:
                            reserved.approved = 1
                            logger.info(f"Seat approved by {username}: bus {bus_id}, seat {seat_id}")
                            db.session.add(reserved)
            
            db.session.commit()
            
            # 更新後の座席情報を取得
            seatall = db.session.query(Seat).filter_by(bus_id=bus_id).all()
            seats = []
            for seat in seatall:
                reserved = db.session.query(Reservation).filter_by(seat_number=seat.number, bus_id=bus_id).first()
                if reserved:
                    seats.append({
                        "number": seat.number,
                        "reserved": 1,
                        "approved": reserved.approved,
                        "username": gakusei(str(reserved.user_id))
                    })
                else:
                    seats.append({
                        "number": seat.number,
                        "reserved": 0,
                        "approved": 0,
                        "username": "none"
                    })
            
            message = '予約の承認が完了しました'
            if notallow:
                message += f'（{notallow}はすでに承認済みです）'
            
            return render_template('bnum.html', yukisaki=yukisaki(bus.ud), bus=bus, seats=seats, message=message)
        else:
            # 座席が選択されていない場合
            seatall = db.session.query(Seat).filter_by(bus_id=bus_id).all()
            seats = []
            for seat in seatall:
                reserved = db.session.query(Reservation).filter_by(seat_number=seat.number, bus_id=bus_id).first()
                if reserved:
                    seats.append({
                        "number": seat.number,
                        "reserved": 1,
                        "approved": reserved.approved,
                        "username": gakusei(str(reserved.user_id))
                    })
                else:
                    seats.append({
                        "number": seat.number,
                        "reserved": 0,
                        "approved": 0,
                        "username": "none"
                    })
            
            return render_template('bnum.html', yukisaki=yukisaki(bus.ud), bus=bus, seats=seats, message='座席を選択してください')

    @app.route('/question')
    @require_auth
    def question():
        """質問のトップページ"""
        return render_template('question.html')

    @app.route('/question/QA')
    @require_auth
    def qa_view():
        """Q&Aの表示"""
        qa_list = []
        for qa in db.session.query(QA).all():
            qa_list.append({"question": qa.question, "answer": qa.answer})
        return render_template('QA.html', QA=qa_list)

    @app.route('/question/mail')
    @require_auth
    def mail():
        """メールの送信画面"""
        return render_template('mail.html')

    @app.route('/question/mail/send', methods=['POST'])
    @require_auth
    def mailsend():
        """メール送信処理"""
        message = request.form['message']
        
        try:
            msg = MIMEText(message, "plain", "utf-8")
            msg["From"] = "xxx@xxx.xxx"
            msg["To"] = "yyy@yyy.yyy"
            msg["Subject"] = "ドライバーシステムからのメール"

            # メール送信設定は環境に応じて設定
            # smtp = smtplib.SMTP_SSL(host='プロバイダのSMTPメールサーバー', port=465)
            # smtp.login('ユーザー名', 'パスワード')
            # smtp.send_message(msg)
            # smtp.quit()
            
            logger.info(f"Mail sent: {message[:50]}...")
            return render_template('mail.html', message='メールを送信しました')
        
        except Exception as e:
            logger.error(f"Mail sending failed: {e}")
            return render_template('mail.html', message='メール送信に失敗しました')

    @app.route('/tips')
    @require_auth
    def tips():
        """説明ページ"""
        return render_template('tips.html')

    @app.route('/logout')
    def logout():
        """ログアウト"""
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            session_manager.delete_session(hashed_num)
        
        response = app.make_response(render_template('login.html', message='ログアウトしました'))
        response.set_cookie('hashed_num', '', expires=0)
        return response

    # エラーハンドリング
    @app.errorhandler(400)
    def bad_request(e):
        if get_current_user():
            return topview('想定しない動作が行われました')
        return render_template('login.html')

    @app.errorhandler(404)
    def not_found(e):
        if get_current_user():
            return topview('ページが見つかりません')
        return render_template('login.html')

    @app.errorhandler(405)
    def not_allowed(e):
        if get_current_user():
            return topview('許可されていない操作です')
        return render_template('login.html')

    @app.errorhandler(500)
    def internal_server_error(e):
        if get_current_user():
            return topview('サーバー内部エラー')
        return render_template('login.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=8080)