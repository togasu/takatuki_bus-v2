"""予約関連のルーティング"""

from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, timedelta
from app.utils.helper_functions import get_authenticated_user, yukisaki
from app.services import BusService, SeatService
from app.models import Bus
from app.database import db
import traceback

yoyaku_bp = Blueprint('yoyaku', __name__, url_prefix='/yoyaku')


@yoyaku_bp.route('', strict_slashes=False)
@yoyaku_bp.route('/')
def yoyaku():
    """予約の日付選択画面"""
    user = get_authenticated_user()
    if user:
        today = datetime.now().date()
        nextday = today + timedelta(days=1)
        return render_template('date_select.html', today=today, nextday=nextday)
    return render_template('login.html')

@yoyaku_bp.route('/bus', methods=['POST'], strict_slashes=False)
def yoyaku_bus_select():
    """バスの一覧を表示する画面"""
    try:
        user = get_authenticated_user()
        if not user:
            return render_template('login.html')
        
        today = datetime.now().date()
        nextday = today + timedelta(days=1)        
        
        date_str = request.form.get('selected-date')
        if not date_str:
            return render_template('date_select.html', today=today, nextday=nextday, message='日付を選択してください')
        
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        ud = request.form.get('selected-destination')
        
        if not ud:
            return render_template('date_select.html', today=today, nextday=nextday, message='行き先を選択してください')

        buses = BusService.get_buses_by_date_and_direction(date, ud)
        print(f"Found buses: {buses}")
        return render_template('bus_select.html', buses=buses)
    except ValueError as e:
        print(f"ValueError in yoyaku_bus_select: {e}")
        print(traceback.format_exc())
        today = datetime.now().date()
        nextday = today + timedelta(days=1)
        return render_template('date_select.html', today=today, nextday=nextday, message='日付の形式が正しくありません'), 400
    except Exception as e:
        print(f"Error in yoyaku_bus_select: {e}")
        print(traceback.format_exc())
        return jsonify({
            'error': True,
            'error_type': type(e).__name__,
            'message': '予期しないエラーが発生しました',
            'detail': str(e)
        }), 500


@yoyaku_bp.route('/bus/<bus_id>')
def yoyaku_bus(bus_id):
    """予約の座席選択画面"""
    try:
        user = get_authenticated_user()
        if not user:
            return render_template('login.html')
        
        bus = db.session.query(Bus).filter_by(id=bus_id).first()
        if not bus:
            return render_template('yoyaku.html', message='バスが見つかりません'), 404
        
        seats = SeatService.get_seats_with_reservations(bus_id)
        return render_template('bnum.html', yukisaki=yukisaki(bus.ud), bus=bus, seats=seats)
    except Exception as e:
        print(f"Error in yoyaku_bus: {e}")
        print(traceback.format_exc())
        return jsonify({
            'error': True,
            'error_type': type(e).__name__,
            'message': '予期しないエラーが発生しました',
            'detail': str(e)
        }), 500


@yoyaku_bp.route('/bus/<int:bus_id>/reserve', methods=['POST'])
def reserve(bus_id):
    """予約の処理を行うルーティング（運転手による座席登録機能）"""
    try:
        user = get_authenticated_user()
        if not user:
            return render_template('login.html')
        
        bus = db.session.query(Bus).filter_by(id=bus_id).first()
        if not bus:
            return jsonify({
                'error': True,
                'error_type': 'NotFound',
                'message': 'バスが見つかりません'
            }), 404
        
        seat_ids = request.form.getlist('seat_numbers')
        print(f"seats: {seat_ids}")
        
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
    except Exception as e:
        print(f"Error in reserve: {e}")
        print(traceback.format_exc())
        return jsonify({
            'error': True,
            'error_type': type(e).__name__,
            'message': '予期しないエラーが発生しました',
            'detail': str(e)
        }), 500