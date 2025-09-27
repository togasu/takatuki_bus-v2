from flask import Flask, render_template, make_response, request, url_for, g
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
import json, logging
import random, hashlib
from random import randint
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
from email.mime.multipart import MIMEMultipart

def driver():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///driver.db'
    app.config['SQLALCHEMY_BINDS'] = {'db2':'sqlite:///hash.db',
                                    'db3':'sqlite:///../../yoyaku_system/instance/yoyaku_seki.db'}

    db = SQLAlchemy(app)

    #ログ設定
    logger = logging.getLogger('sojo-bus-log')
    logger.setLevel(10)
    sh = logging.StreamHandler()
    logger.addHandler(sh)
    fh = logging.FileHandler('sojo-bus.log')
    logger.addHandler(fh)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.info('stating sojo-bus server')

    # ユーザー情報を格納するテーブル
    class Driver(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False) #ユーザー名
        number = db.Column(db.Integer, unique=True, nullable=False) #運転手番号
        password = db.Column(db.String, unique=False, nullable=False) # パスワード(暗号化)
        salt = db.Column(db.String, unique=False, nullable=False) # パスワードの暗号化に使用するsalt

    # Q&Aを格納するテーブル
    class QA(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        question = db.Column(db.String(80), unique=False, nullable=False) #質問
        answer = db.Column(db.String(80), unique=False, nullable=False) #回答
        createuser = db.Column(db.String(80), unique=False, nullable=False) #作成者
        createdate = db.Column(db.DateTime, nullable=False) #作成日時

    # ハッシュ化された番号を格納するテーブル
    class Hash(db.Model):
        __bind_key__ = "db2"
        id = db.Column(db.Integer, primary_key=True)
        hashed_num = db.Column(db.String, unique=True, nullable=False)
        username = db.Column(db.String(80), unique=False, nullable=False)
        last_login = db.Column(db.DateTime, unique=False, nullable=False)

    # バスの情報を格納するテーブル
    class Bus(db.Model):
        __bind_key__ = "db3"
        id = db.Column(db.Integer, primary_key=True)
        busid = db.Column(db.Integer, nullable=False)
        departure_time = db.Column(db.DateTime, nullable=False)
        seats = db.Column(db.Integer,nullable=False)
        ud = db.Column(db.Integer,nullable=False)  #上りなら0、下りなら1
        bookable_time = db.Column(db.Integer,nullable=False) #デフォルト0,予約可能時間に合わせて変更
        status = db.Column(db.Integer,nullable=False)

    class Seat(db.Model):
        __bind_key__ = "db3"
        id = db.Column(db.Integer, primary_key=True)
        number = db.Column(db.Integer, nullable=False)
        bus_id = db.Column(db.Integer, nullable=False) # Bus.idを入れている
        reservations = db.relationship('Reservation', backref='seat', lazy=True)

    class Reservation(db.Model):
        __bind_key__ = "db3"
        __tablename__ = 'Reservation' #テーブル名を指定
        id = db.Column(db.Integer, primary_key=True)
        seat_number = db.Column(db.Integer, db.ForeignKey('seat.number'), nullable=False)
        bus_id = db.Column(db.Integer, db.ForeignKey('bus.id'), nullable=False)
        user_id = db.Column(db.Integer, nullable=False)
        approved = db.Column(db.Integer,nullable=False) # 0なら未認証(デフォルト)、1なら認証済み
        reserved_time = db.Column(db.DateTime)

    with app.app_context():
        db.create_all()

    #cookieに関する補助関数はなぜ動いているのかわかっていません。
    #cookieに追加するための補助関数
    def add_cookie(key, value):
        if not hasattr(g, 'cookies'):
            g.cookies = {}
        g.cookies[key] = value

    #responseなしでhashに追加を行うための補助関数
    @app.after_request
    def apply_cookies(response):
        if hasattr(g, 'cookies'):
            for key, value in g.cookies.items():
                response.set_cookie(key, value)
        return response

    # ログイン時にハッシュ化された番号を生成する関数
    def hash_login(username):
        try : 
            hashed_num = db.session.query(Hash).filter_by(username=username).first()
            db.session.delete(hashed_num)
            db.session.commit()
        except :
            pass
        username = db.session.query(Driver).filter_by(username=username).first().username
        hashed_num = username + str(random.randint(0,1000000)) + str(datetime.now()) # ハッシュ化するための文字列。ユーザー名、乱数、現在時刻を結合。passwordは意図して含んでいない。
        hashed_num = hashlib.sha256(hashed_num.encode()).hexdigest() # ハッシュ化
        hash_entry = Hash(hashed_num=hashed_num, username=username, last_login=datetime.now())
        db.session.add(hash_entry)
        db.session.commit()
        add_cookie('hashed_num', hashed_num)
        return hashed_num

    # ハッシュ化された番号をチェックする関数
    def Hash_check(hashed_num):
        user = Hash.query.filter_by(hashed_num=hashed_num).first()
        print(user)
        username = user.username[0:6]
        if username == "driver":
            if user.last_login > datetime.now() - timedelta(days=1):
                pass
            else :
                hash_entry = db.session.query(Hash).filter_by(username=user.username).first()
                db.session.delete(hash_entry)
                db.session.commit()
                hashed_num = user.username + str(random.randint(0,1000000)) + str(datetime.now()) # ハッシュ化するための文字列。ユーザー名、乱数、現在時刻を結合。passwordは意図して含んでいない。
                hashed_num = hashlib.sha256(hashed_num.encode()).hexdigest() # ハッシュ化
                hash_entry = Hash(hashed_num=hashed_num, username=user.username, last_login=datetime.now())
                db.session.commit()
                db.session.add(hash_entry)
                add_cookie('hashed_num', hashed_num)
            return user.username
        return render_template('login.html', message='ハッシュが切れました')

    #passwordの暗号化の合致テスト
    def verify_password(stored_password, stored_salt, provided_password):
        library_hashed = hashlib.pbkdf2_hmac(
            'sha256', provided_password.encode('utf-8'), stored_salt, 1000
        )
        return library_hashed == stored_password

    # 行き先の文字化です。
    def yukisaki(ud):
        if ud == 0:
            return "高槻キャンパス"
        else:
            return "高槻駅"

    def topview(message): #topルーティングとloginregister以外で使うとき
        num = request.cookies.get('hashed_num')
        num = Hash_check(num)
        num = int(num[6])
        now = datetime.now()
        try:
            firstbus = db.session.query(Bus).filter(Bus.departure_time > datetime.now(),Bus.busid==num).first()
            firstbusdate = firstbus.departure_time
            ud = yukisaki(firstbus.ud)
            firstbus = {"busid": firstbus.busid, "departure_time": str(firstbus.departure_time.strftime('%m/%d %H:%M')), "ud": ud}
            firstbus = str(f"行き先|{firstbus['ud']}  出発時刻|{firstbus['departure_time']} {firstbus['busid']}号車")
        except:
            firstbus = "バスがありません"
        try:
            print(firstbus.departure_time)
            secoundbus = db.session.query(Bus).filter(Bus.departure_time > firstbusdate,Bus.busid==num).first()
            print(secoundbus)
            ud = yukisaki(secoundbus.ud)
            secoundbus = {"busid": secoundbus.busid, "departure_time": str(secoundbus.departure_time.strftime('%m/%d %H:%M')), "ud": ud}
            secoundbus = str(f"行き先|{secoundbus['ud']}  出発時刻|{secoundbus['departure_time']} {secoundbus['busid']}号車")
        except:
            secoundbus = "バスがありません"
        return render_template('top.html', firstbus=firstbus, secoundbus=secoundbus, message=message)

    # ログイン画面です。
    @app.route('/login')
    def login():
        return render_template('login.html')

    # ログイン処理です。ユーザー名とパスワードを受け取り、ハッシュ化された番号を生成します。
    @app.route('/login/register', methods=['POST'])
    def login_register():
        username = request.form['username']
        password = request.form['password']
        print(f"login: {username},{password}")
        user = db.session.query(Driver).filter_by(username=username).first()
        if user:
            stored_password = user.password
            stored_salt = user.salt
            if not verify_password(stored_password, stored_salt, password):
                return render_template('login.html', message = 'パスワードが間違っています')
        else:
            return render_template('login.html', message = 'ユーザー名が間違っています')
        hashed_num = hash_login(username)
        print(f"hash : {hashed_num}")
        if hashed_num is None:
            return render_template('login.html', message='Hash化に失敗しました')
        try:
            firstbus = db.session.query(Bus).filter(Bus.departure_time > datetime.now(), Bus.busid == int(user[6])).first()
            firstbusdate = firstbus.departure_time
            ud = yukisaki(firstbus.ud)
            firstbus = {"busid": firstbus.busid, "departure_time": str(firstbus.departure_time.strftime('%m/%d %H:%M')), "ud": ud}
            firstbus = str(f"行き先|{firstbus['ud']}  出発時刻|{firstbus['departure_time']} {firstbus['busid']}号車")
        except:
            firstbus = "バスがありません"
            try:
                print("try")
                print(firstbusdate)
                secoundbus = db.session.query(Bus).filter(Bus.departure_time > firstbusdate, Bus.busid == int(user[6])).first()
                print(secoundbus)
                ud = yukisaki(secoundbus.ud)
                secoundbus = {"busid": secoundbus.busid, "departure_time": str(secoundbus.departure_time.strftime('%m/%d %H:%M')), "ud": ud}
                secoundbus = str(f"行き先|{secoundbus['ud']}  出発時刻|{secoundbus['departure_time']} {secoundbus['busid']}号車")
            except:
                secoundbus = "バスがありません"
            return render_template('top.html', firstbus=firstbus, secoundbus=secoundbus)
        return render_template('login.html', message='Hash化に失敗しました')

    # 運転手用の特殊ログインです。号車番号を指定してログインします。
    @app.route('/login<num>')
    def drivernumlogin(num):
        username = 'driver' + str(num)
        try: 
            user = db.session.query(Driver).filter_by(username=username).first()
            if not user:
                return render_template('login.html', message = 'ユーザー名が間違っています')
            hash_login(username)
            logger.info(f"success to login unten driver {num}")
            return topview('運転手用特殊ログインを行いました')
        except:
            pass
        return render_template('login.html', message = 'ユーザーログインに失敗しました')

    # topページです。ログインしていない場合はログイン画面にリダイレクトします。
    @app.route('/')
    def top():
        try:
            hashed_num = request.cookies.get('hashed_num')
            try:
                user = Hash_check(hashed_num)
                if not user:
                    return render_template('login.html')
                try:
                    firstbus = db.session.query(Bus).filter(Bus.departure_time > datetime.now(), Bus.busid == int(user[6])).first()
                    firstbusdate = firstbus.departure_time
                    ud = yukisaki(firstbus.ud)
                    firstbus = {"busid": firstbus.busid, "departure_time": str(firstbus.departure_time.strftime('%m/%d %H:%M')), "ud": ud}
                    firstbus = str(f"行き先|{firstbus['ud']}  出発時刻|{firstbus['departure_time']} {firstbus['busid']}号車")
                except:
                    firstbus = "バスがありません"
                try:
                    print(firstbusdate)
                    secoundbus = db.session.query(Bus).filter(Bus.departure_time > firstbusdate, Bus.busid == int(user[6])).first()
                    print(secoundbus)
                    ud = yukisaki(secoundbus.ud)
                    secoundbus = {"busid": secoundbus.busid, "departure_time": str(secoundbus.departure_time.strftime('%m/%d %H:%M')), "ud": ud}
                    secoundbus = str(f"行き先|{secoundbus['ud']}  出発時刻|{secoundbus['departure_time']} {secoundbus['busid']}号車")
                except:
                    secoundbus = "バスがありません"
                return render_template('top.html', firstbus=firstbus, secoundbus=secoundbus)
            except:
                print("error")
        except:
            pass
        return render_template('login.html')

    # バスの運行便設定選択画面です。
    @app.route('/bus')
    def bus():
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                number = db.session.query(Driver).filter_by(username=user).first().number
                if number:
                    now = datetime.now()
                    busdate = db.session.query(Bus).filter(Bus.departure_time > now, Bus.busid == number).order_by(Bus.departure_time).limit(5).all()
                    print(busdate)
                    bus_date = []
                    for bus in busdate:
                        bus_date.append({
                            "id" : bus.id,
                            "busid": bus.busid,
                            "departure_time": str(bus.departure_time.strftime('%m/%d %H:%M')),
                            "seats": bus.seats,
                            "ud": bus.ud
                        })
                    return render_template('bus.html', bus_date=bus_date, number=number)
        return render_template('login.html')

    # バスの運行便設定です。
    @app.route('/bus/register')
    def bus_register():
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                user = Driver.query.filter_by(username=user).first()                                                 
                if user:
                    id = request.args.get('id')
                    if not id:
                        return render_template('bus_register.html', message='バスIDと出発時刻を選択してください')
                    print(id)
                    businfo = db.session.query(Bus).filter_by(id=id).first()
                    bus = {
                        "id" : businfo.id,
                        "busid": businfo.busid,
                        "departure_time": str(businfo.departure_time.strftime('%Y/%m/%d %H:%M')),
                        "seats": businfo.seats,
                        "ud": businfo.ud
                    }
                    departure_time = bus["departure_time"]
                    bus_id = bus["busid"]
                    with open (f'../yoyaku_system/bus{bus_id}.json','w') as file:
                        json.dump(bus,file)
                        logger.info(f"success to register unten bus {bus_id}, departure_time {departure_time} bus_id {bus_id}")
                    return render_template('bus_register.html', bus_id=bus_id,departure_time=departure_time)
        return render_template('login.html')

    # 予約の日付選択画面です。
    @app.route('/yoyaku')
    def yoyaku():
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                today = datetime.now().date()
                nextday = today + timedelta(days=1)
                return render_template('date_select.html', today=today, nextday=nextday)
        return render_template('login.html')

    # バスの一覧を表示する画面です。
    @app.route('/yoyaku/bus', methods=['POST'])
    def yoyaku_bus_select():
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            today = datetime.now().date()
            nextday = today + timedelta(days=1)        
            if user:
                date = request.form.get('selected-date')
                date = datetime.strptime(date, '%Y-%m-%d').date()
                ud = request.form.get('selected-destination')
                if not date or not ud:
                    return render_template('date_select.html', today = today, nextday = nextday, message='選択しなおしてください')

                buses = []
                if ud == "高槻キャンパス":
                    if date == today:
                        buses = db.session.query(Bus).filter_by(ud=0).filter(Bus.departure_time > today, Bus.departure_time < nextday).all()
                    elif date == nextday:
                        buses = db.session.query(Bus).filter_by(ud=0).filter(Bus.departure_time > nextday, Bus.departure_time < datetime.now() + timedelta(days=2) ).all()
                elif ud == "高槻駅":
                    if date == today:
                        buses = db.session.query(Bus).filter_by(ud=1).filter(Bus.departure_time > today, Bus.departure_time < nextday).all()
                    elif date == nextday:
                        buses = db.session.query(Bus).filter_by(ud=1).filter(Bus.departure_time > nextday, Bus.departure_time < datetime.now() + timedelta(days=2) ).all()
                else:
                    return render_template('date_select.html', today = today, nextday = nextday, message='選択しなおしてください')
                print(buses)
                return render_template('bus_select.html', buses=buses)
        return render_template('login.html')

    def gakusei(username):
        if len(username) in [1,2,3,4]:
            username = "driver" + username
        elif len(username) < 6:
            username = "使用不可"
        elif len(username) == 6:
            username = "情" + username[:2] + "-" + username[-4:]
        #大学院生の場合
        elif str(username)[2] == "1":
            username = "情" + str(username[:2]) + "M" + str(username[4:])
        else:
            username = "情" + username[:2] + "D" + username[4:]
        return username

    # 予約の座席選択画面です。backlogにより、追加された運転手による座席登録機能の要素が多いです。
    @app.route('/yoyaku/bus/<bus_id>')
    def yoyaku_bus(bus_id):
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                bus = db.session.query(Bus).filter_by(id=bus_id).first()
                if bus:
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
                    return render_template('bnum.html', yukisaki=yukisaki(bus.ud) ,bus=bus, seats=seats)
                else:
                    return render_template('yoyaku.html', message='バスが見つかりません')
        return render_template('login.html')

    # 予約の処理を行うルーティングです。backlogにより、追加された運転手による座席登録機能です。
    @app.route('/yoyaku/bus/<int:bus_id>/reserve', methods=['POST'])
    def reserve(bus_id):
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            print(user)
            if user:
                seat_ids = request.form.getlist('seat_numbers')
                print(f"seats{seat_ids}")
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
                                    logger.info(f"success to approved {user} / {bus_id}, seat {seat_id}")
                                    db.session.add(reserved)
                            else:
                                pass
                                # 予約処理
                                #userid = db.session.query(Driver).filter_by(username=user).first().number
                                # 運転手のため認証は済んでいるものとしています。
                                #reservation = Reservation(user_id=userid, bus_id=bus_id, seat_number=seat_id, approved=1, reserved_time=datetime.now())
                                #logger.info(f"success to reserve {user} / {bus_id}, seat {seat_id}")
                                #db.session.add(reservation)
                    db.session.commit()
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
                    return render_template('bnum.html', yukisaki = yukisaki(bus.ud), bus=bus,seats=seats, notallow=f'{notallow}はすでに予約されています', message='予約が完了しました')
                else:
                    seats = []
                    seatall = db.session.query(Seat).filter_by(bus_id=bus_id).all()
                    for seat in seatall:
                        reserved = db.session.query(Reservation).filter_by(seat_number=seat.number, bus_id=bus_id).first()
                        if reserved:
                            seats.append({
                                "number": seat.number,
                                "reserved": 1,
                                "approved": reserved.approved
                            })
                        else:
                            seats.append({
                                "number": seat.number,
                                "reserved": 0,
                                "approved": 0
                            })
                    return render_template('bnum.html', yukisaki=yukisaki(bus.ud), bus=bus, seats=seats, message='座席を選択してください')
        return render_template('login.html')

    # 質問のトップページです。これも簡素。
    @app.route('/question')
    def question():
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                return render_template('question.html')
        return render_template('login.html')

    # Q&Aの表示です。Q&Aの追加は事務システムから行えるようにする予定です。
    @app.route('/question/QA')
    def QA():
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                QandA = [] 
                for qa in db.session.query(QA).all():    
                    QandA.append({"question":qa.question, "answer":qa.answer})
                return render_template('QA.html', QA=QandA)
        return render_template('login.html')

    # メールの送信画面です。すごい簡素なのでどうにかしないといけない。
    @app.route('/question/mail')
    def mail():
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                return render_template('mail.html')
        return render_template('login.html')

    # メールです。メールの送信先はメルアド発効後に設定とします。
    @app.route('/question/mail/send', methods=['POST'])
    def mailsend():
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                message = request.form['message']  
                msg = MIMEText(message, "plain", "utf-8")
                msg["From"] = "xxx@xxx.xxx"
                msg["To"] = "yyy@yyy.yyy"
                msg["Subject"] = "メールの件名"

                smtp = smtplib.SMTP_SSL(host = 'プロバイダのSMTPメールサーバー', port = 465)
                smtp.login('ユーザー名', 'パスワード')
                smtp.send_message(msg)
                smtp.quit()
                return render_template('mail.html', message='メールを送信しました')
        return render_template('login.html')

    # 説明ページ
    # 一枚でまとまらなれば下位ページも作ります。
    @app.route('/tips')
    def tips():
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                return render_template('tips.html')
        return render_template('login.html')

    # エラーハンドリング
    @app.errorhandler(400)
    def bad_request(e):
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                return topview('想定しない動作が行われました')
        return render_template('login.html')

    @app.errorhandler(404)
    def not_found(e):
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                return topview('ページが見つかりません')
        return render_template('login.html')

    @app.errorhandler(405)
    def not_allowed(e):
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                return topview('値がありません')
        return render_template('login.html')

    @app.errorhandler(500)
    def internal_server_error(e):
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            user = Hash_check(hashed_num)
            if user:
                return topview('サーバー内部エラー')
        return render_template('login.html')
    
    return app

'''
if __name__ == '__main__':
    app.run(debug=True, port=8080)
'''