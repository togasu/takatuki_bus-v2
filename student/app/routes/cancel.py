from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import logging
from ..models.bus import db, Bus
from ..models.seat import Seat
from ..models.reservation import Reservation
from ..models.user import User_Penalty
from ..models.cancel import Cancel
from ..utils.auth_utils import check_session

cancel_bp = Blueprint('cancel', __name__)

# ロガーの設定
logger = logging.getLogger('sojo-bus-log')

@cancel_bp.route('/cancel/check')
def cancelcheck():
    token = request.cookies.get('token')
    data = check_session(token)
    if data['flag'] == False:
        return redirect(url_for('auth.top'))
    
    # ユーザータイプに応じて識別子を設定（booking.pyと同じロジック）
    if data.get('type') == 'admin_user':
        username = f"admin_{data.get('username')}"
    elif data.get('type') == 'driver_user':
        username = f"driver_{data.get('username')}"
    else:
        username = data.get('student_id')
    
    bus_data = db.session.query(Reservation).filter_by(user_id=username).order_by(Reservation.bus_id).all()
    for bus in bus_data[:]:
        reservation = db.session.query(Bus).filter_by(id=bus.bus_id).first()
        if datetime.now() >= reservation.departure_time:
            bus_data.remove(bus)
    print(bus_data)
    
    bus_info_list = []
    if len(bus_data) != 0:
        for bus in bus_data:
            bus_data_info = db.session.query(Bus).filter_by(id=bus.bus_id).first()
            print(bus.bus_id, bus_data_info.busid)
            bus_info = {
                "id": bus.bus_id,
                "busid": bus_data_info.busid,
                "departure_time": str(bus_data_info.departure_time.strftime('%m/%d %H:%M')),
                "busseat": bus.seat_number,
                "int": True
            }
            bus_info_list.append(bus_info)
            
        return render_template('reservation_cancel_list.html', bus_data=bus_info_list)
    else:
        return render_template('reservation_cancel_list.html')

@cancel_bp.route('/cancel/<bus_id>')
def cancel(bus_id):
    token = request.cookies.get('token')
    data = check_session(token)
    if data['flag'] == False:
        return redirect(url_for('auth.top'))
    
    return render_template('cancel.html', bus_id=bus_id)

@cancel_bp.route('/cancel/<bus_id>/delete')
def cancelation(bus_id):
    from ..utils.redis_lock import redis_lock, get_redis_client
    
    token = request.cookies.get('token')
    data = check_session(token)
    if data['flag'] == False:
        return redirect(url_for('auth.top'))
    
    # ユーザータイプに応じて識別子を設定（booking.pyと同じロジック）
    if data.get('type') == 'admin_user':
        username = f"admin_{data.get('username')}"
    elif data.get('type') == 'driver_user':
        username = f"driver_{data.get('username')}"
    else:
        username = data.get('student_id')

    print(username, bus_id)
    
    # Redis接続を取得
    redis_client = get_redis_client()
    if not redis_client:
        return render_template('cancel_failed.html'), 500
    
    try:
        # ユーザーの予約を確認してロックキーを生成
        reservationdata = db.session.query(Reservation).filter_by(user_id=username, bus_id=bus_id).first()
        print(reservationdata)
        
        if not reservationdata:
            return render_template('cancel_failed.html'), 400
            
        # 分散ロック用のキーを生成
        lock_key = f"seat_reservation:{bus_id}:{reservationdata.seat_number}"
        
        # 分散ロックを使用してキャンセル処理を安全に実行
        with redis_lock(redis_client, lock_key, timeout=30, retry_delay=0.1):
            # 最新の予約データを再取得
            reservationdata = db.session.query(Reservation).filter_by(user_id=username, bus_id=bus_id).first()
            if reservationdata:
                bus_reservation = db.session.query(Reservation).filter_by(bus_id=bus_id).count()
                bus = db.session.query(Bus).filter_by(id=bus_id).first()
                print(f"delete by {reservationdata.user_id} ,bus_id : {reservationdata.bus_id}, seat_number : {reservationdata.seat_number}")
                seat_number = reservationdata.seat_number
                cancel = Cancel(student_id=username, bus_id=bus_id, seat_number=seat_number, cancel_time=datetime.now(), status="Cancel")
                db.session.add(cancel)
                db.session.commit()
                db.session.delete(reservationdata)
                db.session.commit()
                logger.info(f"success to cancel from {username}. The bus_id is {bus_id}, seat_number is {seat_number}. The time is {datetime.now()}.")

                # WebSocketでリアルタイム更新をブロードキャスト
                try:
                    from flask import current_app
                    if hasattr(current_app, 'socketio'):
                        from .ws import broadcast_bus_update
                        broadcast_bus_update(current_app.socketio)
                except Exception as ws_error:
                    print(f"WebSocket更新エラー: {ws_error}")

                if bus_reservation == bus.seats:
                    try:
                        with open('wait_cancel.json', mode='a') as f:
                            f.write(f"{bus_id} {seat_number}")
                            f.write("\n")
                        return render_template('cancel_success.html'), 200
                    except:
                        return render_template('cancel_failed.html'), 400
                else:
                    return render_template('cancel_success.html'), 200
            else:
                return render_template('cancel_failed.html'), 400
                
    except TimeoutError:
        return render_template('cancel_failed.html'), 429
    except Exception as e:
        print(f"キャンセル処理エラー: {e}")
        return render_template('cancel_failed.html'), 500
