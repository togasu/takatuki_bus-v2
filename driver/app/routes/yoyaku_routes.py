"""予約関連のルーティング"""

from flask import Blueprint, render_template, request
from datetime import datetime, timedelta
from app.utils.helper_functions import get_authenticated_user, yukisaki
from app.services import BusService, SeatService
from app.models import Bus
from app.database import db

yoyaku_bp = Blueprint('yoyaku', __name__, url_prefix='/yoyaku')


@yoyaku_bp.route('/')
def yoyaku():
    """予約の日付選択画面"""
    user = get_authenticated_user()
    if user:
        today = datetime.now().date()
        nextday = today + timedelta(days=1)
        return render_template('date_select.html', today=today, nextday=nextday)
    return render_template('login.html')


@yoyaku_bp.route('/bus', methods=['POST'])
def yoyaku_bus_select():
    """バスの一覧を表示する画面"""
    user = get_authenticated_user()
    if user:
        today = datetime.now().date()
        nextday = today + timedelta(days=1)        
        
        date = request.form.get('selected-date')
        date = datetime.strptime(date, '%Y-%m-%d').date()
        ud = request.form.get('selected-destination')
        
        if not date or not ud:
            return render_template('date_select.html', today=today, nextday=nextday, message='選択しなおしてください')

        buses = BusService.get_buses_by_date_and_direction(date, ud)
        print(buses)
        return render_template('bus_select.html', buses=buses)
    return render_template('login.html')


@yoyaku_bp.route('/bus/<bus_id>')
def yoyaku_bus(bus_id):
    """予約の座席選択画面"""
    user = get_authenticated_user()
    if user:
        bus = db.session.query(Bus).filter_by(id=bus_id).first()
        if bus:
            seats = SeatService.get_seats_with_reservations(bus_id)
            return render_template('bnum.html', yukisaki=yukisaki(bus.ud), bus=bus, seats=seats)
        else:
            return render_template('yoyaku.html', message='バスが見つかりません')
    return render_template('login.html')


@yoyaku_bp.route('/bus/<int:bus_id>/reserve', methods=['POST'])
def reserve(bus_id):
    """予約の処理を行うルーティング（運転手による座席登録機能）"""
    user = get_authenticated_user()
    if user:
        seat_ids = request.form.getlist('seat_numbers')
        print(f"seats{seat_ids}")
        
        bus = db.session.query(Bus).filter_by(id=bus_id).first()                
        
        if seat_ids:
            notallow = SeatService.approve_reservations(bus_id, seat_ids)
            seats = SeatService.get_seats_with_reservations(bus_id)
            
            notallow_message = f'{notallow}はすでに予約されています' if notallow else ''
            return render_template('bnum.html', 
                                   yukisaki=yukisaki(bus.ud), 
                                   bus=bus, 
                                   seats=seats, 
                                   notallow=notallow_message, 
                                   message='予約が完了しました')
        else:
            seats = SeatService.get_seats_with_reservations(bus_id)
            return render_template('bnum.html', 
                                   yukisaki=yukisaki(bus.ud), 
                                   bus=bus, 
                                   seats=seats, 
                                   message='座席を選択してください')
    return render_template('login.html')