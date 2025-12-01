from flask import Blueprint, jsonify, request
from ..models.reservation import Reservation
from ..models.user import User
from ..models.bus import db
from ..utils.auth_utils import check_session

seat_info_bp = Blueprint('seat_info', __name__)

@seat_info_bp.route('/api/seat-info/<int:bus_id>/<int:seat_number>', methods=['GET'])
def get_seat_info(bus_id, seat_number):
    """座席の予約者情報を取得（admin/driverのみアクセス可能）"""
    token = request.cookies.get('token')
    data = check_session(token)
    
    if not data or data.get('flag') == False:
        return jsonify({'error': '認証が必要です'}), 401
    
    # admin/driverユーザーのみアクセス可能
    user_type = data.get('type')
    if user_type not in ['admin_user', 'driver_user']:
        return jsonify({'error': 'この機能はadmin/driverのみ利用可能です'}), 403
    
    # 指定された座席の予約情報を取得
    reservation = db.session.query(Reservation).filter_by(
        bus_id=bus_id, 
        seat_number=seat_number
    ).first()
    
    if not reservation:
        return jsonify({
            'reserved': False,
            'message': 'この座席は予約されていません'
        })
    
    # user_idから表示用の情報を取得
    user_id = reservation.user_id
    display_info = {
        'reserved': True,
        'user_id': user_id,
        'reserved_time': reservation.reserved_time.strftime('%Y-%m-%d %H:%M:%S') if reservation.reserved_time else None,
        'approved': reservation.approved
    }
    
    # 学生の場合は学籍番号を整形して表示
    if not user_id.startswith('admin_') and not user_id.startswith('driver_'):
        # 学生IDの場合
        student = db.session.query(User).filter_by(student_id=user_id).first()
        if student:
            # 学部生の場合
            if len(user_id) == 6:
                display_name = user_id[:2] + "-" + user_id[-4:]
            # 大学院生の場合
            elif len(user_id) > 2 and user_id[2] == "1":
                display_name = str(user_id[:2]) + "M" + str(user_id[4:])
            # 博士生の場合
            else:
                display_name = user_id[:2] + "D" + user_id[4:]
            display_info['display_name'] = display_name
            display_info['student_id'] = user_id
        else:
            display_info['display_name'] = user_id
    elif user_id.startswith('admin_'):
        display_info['display_name'] = f"管理者 ({user_id.replace('admin_', '')})"
        display_info['user_type'] = 'admin'
    elif user_id.startswith('driver_'):
        display_info['display_name'] = f"ドライバー ({user_id.replace('driver_', '')})"
        display_info['user_type'] = 'driver'
    
    return jsonify(display_info)
