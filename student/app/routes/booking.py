from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime, timedelta
from ..models.bus import db, Bus
from ..models.seat import Seat
from ..models.reservation import Reservation
from ..utils.auth_utils import check_session

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/select')
def choice():
    token = request.cookies.get('token')
    data = check_session(token)
    if data['flag'] == False:
        return redirect(url_for('auth.top'))

    today = datetime.date(datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d")
    nextday = (datetime.now() + timedelta(days=1) + timedelta(hours=1)).strftime("%Y-%m-%d")

    return render_template('yukisaki.html', today=today, nextday=nextday)

@booking_bp.route('/select/ud', methods=['POST'])
def ud():
    token = request.cookies.get('token')
    data = check_session(token)
    if data['flag'] == False:
        return redirect(url_for('auth.top'))

    selecteddate = request.form.get('selected-date')
    selecteddestination = request.form.get('selected-destination')
    print(selecteddate, selecteddestination)
    if selecteddate:
        if selecteddestination == "高槻キャンパス":
            return redirect(url_for('booking.upchoice', selecteddate=selecteddate))
        elif selecteddestination == "高槻駅":
            return redirect(url_for('booking.downchoice', selecteddate=selecteddate))
        else:
            return redirect(url_for('booking.choice'))
    else:
        return redirect(url_for('booking.choice'))

@booking_bp.route('/choice/up/<selecteddate>')
def upchoice(selecteddate):
    token = request.cookies.get('token')
    data = check_session(token)
    if data['flag'] == False:
        return redirect(url_for('auth.top'))

    if selecteddate is None:
        return redirect(url_for('booking.choice'))

    selecteddate = datetime.strptime(selecteddate, '%Y-%m-%d')
    print(selecteddate)

    # その日の予約可能なバスを取得
    bus_data = db.session.query(Bus).filter(Bus.ud == 0, Bus.status != 2).order_by(Bus.departure_time).all()
    for bus in bus_data[:]:
        time = bus.departure_time.strftime('%Y-%m-%d')
        time = datetime.strptime(time, '%Y-%m-%d')
        if time == selecteddate:
            dt = bus.departure_time
            if datetime.now() >= dt:
                bus_data.remove(bus)
        else:
            bus_data.remove(bus)

    # 必要データを抽出してリストに格納
    bus_info_list = []
    if len(bus_data) != 0:
        for bus in bus_data:
            total_seats = bus.seats
            reserved_seats = db.session.query(Reservation).filter_by(bus_id=bus.id).count()
            available_seats = total_seats - reserved_seats

            bus_info = {
                "id": bus.id,
                "busid": bus.busid,
                "departure_time": str(bus.departure_time.strftime('%m/%d %H:%M')),
                "busseat": available_seats,
                "status": bus.status
            }
            bus_info_list.append(bus_info)

    time = datetime.now().time().strftime('%H:%M')  # 表示時刻変更の場合これを変更
    yukisaki = '高槻キャンパス行き'
    return render_template('yyoyakuchoice.html', bus_data=bus_info_list, day=selecteddate, time=time, yukisaki=yukisaki)

@booking_bp.route('/choice/down/<selecteddate>')
def downchoice(selecteddate):
    token = request.cookies.get('token')
    data = check_session(token)
    if data['flag'] == False:
        return redirect(url_for('auth.top'))

    if selecteddate is None:
        return redirect(url_for('booking.choice'))

    selecteddate = datetime.strptime(selecteddate, '%Y-%m-%d')
    print(selecteddate)

    # その日の予約可能なバスを取得
    bus_data = db.session.query(Bus).filter(Bus.ud == 1, Bus.status != 2).order_by(Bus.departure_time).all()
    for bus in bus_data[:]:
        time = bus.departure_time.strftime('%Y-%m-%d')
        time = datetime.strptime(time, '%Y-%m-%d')
        if time == selecteddate:
            dt = bus.departure_time
            if datetime.now() >= dt:
                bus_data.remove(bus)
        else:
            bus_data.remove(bus)

    # 必要データを抽出してリストに格納
    bus_info_list = []
    if len(bus_data) != 0:
        for bus in bus_data:
            total_seats = bus.seats
            reserved_seats = db.session.query(Reservation).filter_by(bus_id=bus.id).count()
            available_seats = total_seats - reserved_seats

            bus_info = {
                "id": bus.id,
                "busid": bus.busid,
                "departure_time": str(bus.departure_time.strftime('%m/%d %H:%M')),
                "busseat": available_seats,
                "status": bus.status
            }
            bus_info_list.append(bus_info)

    time = datetime.now().time().strftime('%H:%M')  # 表示時刻変更の場合これを変更
    yukisaki = '高槻駅行き'
    return render_template('yyoyakuchoice.html', bus_data=bus_info_list, day=selecteddate, time=time, yukisaki=yukisaki)

@booking_bp.route('/choice/<bus_id>')
def seat(bus_id):
    token = request.cookies.get('token')
    data = check_session(token)
    if data['flag'] == False:
        return redirect(url_for('auth.top'))

    username = data['student_id']

    bus = db.session.query(Bus).filter_by(id=bus_id).first()
    if bus.status != 0:
        return redirect(url_for('booking.wait_cancel_check', bnum=bus_id))
    
    seat_data = db.session.query(Seat).filter_by(bus_id=bus_id).all()
    reservation_date = db.session.query(Reservation).filter_by(bus_id=bus_id).all()
    i = 0
    reservedtf = []
    for seat in seat_data:
        reserved = any(reservation.seat_number == seat.number for reservation in reservation_date)
        my_reserve = db.session.query(Reservation).filter_by(bus_id=bus_id, seat_number=seat.number, user_id=username).first()
        if reserved and my_reserve is None:
            i += 1
        if my_reserve:
            reservedtf.append('2')
        else:
            reservedtf.append('1' if reserved else '0')
    
    if i == bus.seats or bus.status >= 1:
        return render_template('wait_cancel.html', bnum=bus_id)
    
    return render_template('bnum.html', reservedtf=reservedtf, bus_id=bus_id)

@booking_bp.route('/choice/<bus_id>/reserve', methods=['POST'])
def reserve(bus_id):
    from flask import Flask
    from flask_mail import Mail, Message
    import logging
    from ..models.user import User_Penalty
    from ..utils.redis_lock import redis_lock, get_redis_client
    
    token = request.cookies.get('token')
    data = check_session(token)
    if data['flag'] == False:
        return redirect(url_for('auth.top'))

    # User名を保存情報として持つ
    booked = request.form.get('selected_seat')
    username = data['student_id']
    k_number = data['k_number']
    
    print(f"予約処理開始: booked={booked}, username={username}, bus_id={bus_id}, k_number={k_number}")

    # Redis接続を取得
    redis_client = get_redis_client()
    if not redis_client:
        error_message = "システムエラーが発生しました。しばらくしてからお試しください。"
        return render_template('error.html', error_message=error_message), 500

    # 分散ロック用のキーを生成（バス ID + 座席番号）
    lock_key = f"seat_reservation:{bus_id}:{booked}"

    try:
        # 分散ロックを使用して予約処理を安全に実行
        with redis_lock(redis_client, lock_key, timeout=30, retry_delay=0.1):
            penalty = db.session.query(User_Penalty).filter_by(student_id=username).first()
            if penalty and penalty.penalty_count >= 2:
                date = (penalty.penalty_time.date() - datetime.now().date()).days
                error_message = f'ペナルティ期間です:残り{date}日。すでに予約済みの席はそのままお乗りいただけます。'
                return render_template('error.html', error_message=error_message), 410

            # その人が同じ日の２つ目の上りか下りの便を予約しようとしているか確認
            departure = db.session.query(Bus).filter_by(id=bus_id).first()
            if departure is None:
                error_message = "指定されたバスが見つかりません"
                return render_template('error.html', error_message=error_message)
            
            if not(datetime.date(datetime.now() + timedelta(hours=1)) == departure.departure_time.date() or 
                   datetime.date(datetime.now() + timedelta(hours=1)) == departure.departure_time.date() + timedelta(days=-1)):
                error_message = "予約可能な日付ではありません"
                return render_template('error.html', error_message=error_message)
            
            departure_seat = db.session.query(Seat).filter(Seat.bus_id == bus_id, Seat.number == booked).first()
            if departure_seat is None:
                error_message = "座席を指定してください"
                return render_template('error.html', error_message=error_message)

            # そのバスの日時と上りか下りかを取得
            departure_day = departure.departure_time.date()
            departure_ud = departure.ud
            print(departure_day, departure_ud)

            # 予約しようとしている人の今までの予約情報を取得
            busses = db.session.query(Reservation).filter_by(user_id=username).order_by(Reservation.id.desc()).all()
            for bus in busses:
                # 今までの予約情報のバスの情報を取得
                bus_data = db.session.query(Bus).filter_by(id=bus.bus_id).first()
                if departure_day == bus_data.departure_time.date() and departure_ud == bus_data.ud:
                    error_message = "既に別の座席を予約済みです"
                    return render_template('error.html', error_message=error_message)
                
            # 席が空いているか確認（最新データを取得）
            seat = db.session.query(Reservation).filter_by(bus_id=bus_id, seat_number=booked).all()
            print(f"座席確認: bus_id={bus_id}, seat_number={booked}, 既存予約数={len(seat)}")
            if seat:
                print(f"座席が既に予約済み: {[s.user_id for s in seat]}")
                error_message = "別の利用者が登録済みです"
                return render_template('error.html', error_message=error_message)

            # 予約作成とコミット（ロック内で実行）
            reservation = Reservation(seat_number=booked, user_id=username, bus_id=bus_id, approved=0, reserved_time=datetime.now())
            db.session.add(reservation)

            # メール送信とログ記録
            try:
                logger = logging.getLogger('sojo-bus-log')
                logger.info(f"success to reserve {username},{k_number}. The bus_id is {bus_id}, seat_number is {booked}")
                print(f"予約コミット前: reservation作成完了")
                db.session.commit()
                print(f"予約コミット成功: {username}の座席{booked}番予約完了")

                # WebSocketでリアルタイム更新をブロードキャスト
                try:
                    from flask import current_app
                    if hasattr(current_app, 'socketio'):
                        from .ws import broadcast_bus_update
                        broadcast_bus_update(current_app.socketio)
                except Exception as ws_error:
                    print(f"WebSocket更新エラー: {ws_error}")

                # メール送信の実装は省略（Mailオブジェクトの初期化が必要）
                return render_template('success.html'), 200
                
            except Exception as e:
                print(f"予約コミット失敗: {e}")
                db.session.rollback()
                error_message = "予約処理中にエラーが発生しました"
                return render_template('error.html', error_message=error_message)
                
    except TimeoutError:
        error_message = "現在多くのアクセスが集中しています。しばらくしてからお試しください。"
        return render_template('error.html', error_message=error_message), 429
    except Exception as e:
        print(f"予約処理エラー: {e}")
        error_message = "システムエラーが発生しました。しばらくしてからお試しください。"
        return render_template('error.html', error_message=error_message), 500
