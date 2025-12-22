from flask import Blueprint, render_template, request, jsonify
from app.api_client import admin_api
from app.authorization import require_permission
from datetime import datetime
import logging

# ログの設定
logger = logging.getLogger(__name__)

bp = Blueprint('reservations', __name__, url_prefix='/reservations')

@bp.route('/', methods=['GET'])
@require_permission('reservation', 'read')
def index():
    """予約確認のメインページ"""
    return render_template('reservations/index.html')

@bp.route('/search', methods=['GET', 'POST'])
@require_permission('reservation', 'read')
def search():
    """学籍番号による予約検索"""
    if request.method == 'GET':
        return render_template('reservations/search.html')
    
    student_id = request.form.get('student_id', '').strip()
    
    if not student_id:
        return render_template('reservations/search.html', error="学籍番号を入力してください")
    
    try:
        # Student サービスのAPIを使用して予約情報を取得
        result = admin_api.get_student_reservations(student_id)
        
        if not result.get('success'):
            error_message = result.get('message', '予約情報の取得に失敗しました')
            return render_template('reservations/search.html', error=error_message)
        
        reservations = result.get('reservations', [])
        
        return render_template('reservations/search.html', 
                             reservations=reservations, 
                             student_id=student_id)
    
    except Exception as e:
        logger.error(f"Error searching reservations: {e}")
        import traceback
        traceback.print_exc()
        error_message = "予約データの検索中にエラーが発生しました。"
        return render_template('reservations/search.html', 
                             error=error_message)

@bp.route('/bus/<int:bus_id>', methods=['GET'])
@require_permission('reservation', 'read')
def view_bus(bus_id):
    """便ごとの座席予約状況を表示"""
    try:
        # Student サービスのAPIを使用してバスの座席予約状況を取得
        result = admin_api.get_bus_seat_status(bus_id)
        
        if not result.get('success'):
            error_message = result.get('message', 'バス情報の取得に失敗しました')
            return render_template('reservations/bus_seat_view.html', 
                                 error=error_message, 
                                 bus=None, 
                                 seat_status=[])
        
        bus = result.get('bus')
        seat_status = result.get('seat_status', [])
        
        # 上り/下りの表示用テキストを追加
        if bus:
            bus['ud_text'] = '高槻キャンパス行き' if bus.get('ud') == 0 else '高槻駅行き'
        
        return render_template('reservations/bus_seat_view.html', 
                             bus=bus, 
                             seat_status=seat_status)
    
    except Exception as e:
        logger.error(f"Error viewing bus reservations: {e}")
        import traceback
        traceback.print_exc()
        error_message = "バス予約情報の取得中にエラーが発生しました。"
        return render_template('reservations/bus_seat_view.html', 
                             error=error_message,
                             bus=None,
                             seat_status=[])

@bp.route('/bus/list', methods=['GET'])
@require_permission('reservation', 'read')
def bus_list():
    """予約があるバス一覧を表示"""
    try:
        # Student サービスのAPIを使用して予約があるバス一覧を取得
        result = admin_api.get_buses_with_reservations()
        
        if not result.get('success'):
            error_message = result.get('message', 'バス一覧の取得に失敗しました')
            return render_template('reservations/bus_list.html', error=error_message)
        
        buses = result.get('buses', [])
        
        return render_template('reservations/bus_list.html', buses=buses)
    
    except Exception as e:
        logger.error(f"Error listing buses: {e}")
        import traceback
        traceback.print_exc()
        error_message = "バス一覧の取得中にエラーが発生しました。"
        return render_template('reservations/bus_list.html', 
                             error=error_message)
