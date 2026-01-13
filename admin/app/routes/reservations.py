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

@bp.route('/bus/<int:bus_id>', methods=['GET', 'POST'])
@require_permission('reservation', 'read')
def view_bus(bus_id):
    """便ごとの座席予約状況を表示"""
    try:
        # Student サービスのAPIを使用してバスの座席予約状況を取得
        result = admin_api.get_bus_seat_status(bus_id)

        logger.info(f"Bus seat status API raw result type={type(result)}, value={result}")

        # result が期待する dict でない、または success が False の場合はエラー扱い
        if not isinstance(result, dict) or not result.get('success'):
            # エラーメッセージを可能な限り取り出す
            if isinstance(result, dict):
                error_message = result.get('message', 'バス情報の取得に失敗しました')
            else:
                error_message = f'無効なレスポンス: {result}'

            logger.error(f"Failed to get bus seat status: {error_message}")
            # ここではテンプレートに空の seat_status ではなく、全席空の reservedtf を渡して
            # 座席レイアウト自体は表示させる（情報取得エラーは画面上に出す）
            return render_template('reservations/bus_seat_view.html', 
                                 error=error_message, 
                                 bus=None, 
                                 seat_status=[],
                                 reservedtf=['0'] * 27,
                                 bus_id=bus_id,
                                 is_privileged_user=True)
        
        bus = result.get('bus')
        seat_status = result.get('seat_status', []) if isinstance(result.get('seat_status', []), list) else []

        logger.info(f"Seat status count: {len(seat_status)}")
        logger.debug(f"Full seat_status payload: {seat_status}")
        
        # 上り/下りの表示用テキストを追加
        if bus:
            bus['ud_text'] = '高槻キャンパス行き' if bus.get('ud') == 0 else '高槻駅行き'
        
        # 座席状態リスト（27席分）を作成
        # '0': 空席, '1': 予約済み, その他: ユーザーIDなど
        reservedtf = ['0'] * 27  # 初期状態は全席空席
        
        for seat_info in seat_status:
            try:
                seat_number = int(seat_info.get('seat_number', 0)) if seat_info.get('seat_number') is not None else 0
            except (ValueError, TypeError):
                seat_number = 0

            if 1 <= seat_number <= 27:
                # student サービス側のレスポンスは 'user_id' または 'student_id' を含むはず
                if seat_info.get('user_id') or seat_info.get('student_id'):
                    reservedtf[seat_number - 1] = '1'  # 予約済み
        
        return render_template('reservations/bus_seat_view.html', 
                             bus=bus, 
                             seat_status=seat_status,
                             reservedtf=reservedtf,
                             bus_id=bus_id,
                             is_privileged_user=True)
    
    except Exception as e:
        logger.error(f"Error viewing bus reservations: {e}")
        import traceback
        traceback.print_exc()
        error_message = "バス予約情報の取得中にエラーが発生しました。"
        return render_template('reservations/bus_seat_view.html', 
                             error=error_message,
                             bus=None,
                             seat_status=[],
                             reservedtf=[],
                             bus_id=bus_id,
                             is_privileged_user=True)

@bp.route('/bus/list', methods=['GET'])
@require_permission('reservation', 'read')
def bus_list():
    """すべてのバス一覧を表示（ソート機能付き）"""
    try:
        # ソートパラメータを取得
        sort_by = request.args.get('sort_by', 'departure_time')  # デフォルトは出発時刻
        order = request.args.get('order', 'asc')  # デフォルトは昇順
        
        # Student サービスのAPIを使用してすべてのバス一覧を取得
        result = admin_api.get_buses()
        
        if not result:
            error_message = 'バス一覧の取得に失敗しました'
            return render_template('reservations/bus_list.html', error=error_message, sort_by=sort_by, order=order)
        
        # レスポンスが辞書形式の場合とリスト形式の場合に対応
        if isinstance(result, dict):
            if not result.get('success'):
                error_message = result.get('message', 'バス一覧の取得に失敗しました')
                return render_template('reservations/bus_list.html', error=error_message, sort_by=sort_by, order=order)
            buses = result.get('buses', [])
        elif isinstance(result, list):
            buses = result
        else:
            error_message = '無効なレスポンス形式です'
            return render_template('reservations/bus_list.html', error=error_message, sort_by=sort_by, order=order)
        
        # 各バスに予約数情報を取得して追加
        for bus in buses:
            reservation_result = admin_api.get_bus_seat_status(bus['id'])
            if reservation_result and reservation_result.get('success'):
                seat_status = reservation_result.get('seat_status', [])
                # 予約数をカウント
                bus['reservation_count'] = sum(1 for seat in seat_status if seat.get('user_id') or seat.get('student_id'))
            else:
                bus['reservation_count'] = 0
        
        # ソート処理
        reverse = (order == 'desc')
        if sort_by == 'departure_time':
            buses.sort(key=lambda x: x.get('departure_time') or '', reverse=reverse)
        elif sort_by == 'reservation_count':
            buses.sort(key=lambda x: x.get('reservation_count', 0), reverse=reverse)
        elif sort_by == 'route_name':
            buses.sort(key=lambda x: x.get('route_name') or '', reverse=reverse)
        elif sort_by == 'occupancy_rate':
            buses.sort(key=lambda x: (x.get('reservation_count', 0) / x.get('seats', 1) * 100) if x.get('seats', 0) > 0 else 0, reverse=reverse)
        
        return render_template('reservations/bus_list.html', buses=buses, sort_by=sort_by, order=order)
    
    except Exception as e:
        logger.error(f"Error listing buses: {e}")
        import traceback
        traceback.print_exc()
        error_message = "バス一覧の取得中にエラーが発生しました。"
        return render_template('reservations/bus_list.html', 
                             error=error_message, sort_by='departure_time', order='asc')

@bp.route('/api/seat-info/<int:bus_id>/<int:seat_number>', methods=['GET'])
@require_permission('reservation', 'read')
def get_seat_info(bus_id, seat_number):
    """特定座席の予約情報を取得するAPI（管理者用）"""
    try:
        # Student サービスのAPIを使用して座席情報を取得
        result = admin_api.get_bus_seat_status(bus_id)
        
        if not result.get('success'):
            return jsonify({
                'success': False,
                'message': 'バス情報の取得に失敗しました'
            }), 400
        
        seat_status = result.get('seat_status', [])
        
        # 指定された座席番号の情報を検索
        for seat_info in seat_status:
            if seat_info.get('seat_number') == seat_number:
                if seat_info.get('user_id'):
                    return jsonify({
                        'reserved': True,
                        'user_id': seat_info.get('user_id'),
                        'display_name': seat_info.get('display_name', seat_info.get('user_id')),
                        'student_id': seat_info.get('student_id'),
                        'reserved_time': seat_info.get('reserved_time'),
                        'approved': seat_info.get('approved', 0)
                    })
                else:
                    return jsonify({
                        'reserved': False,
                        'message': 'この座席は予約されていません'
                    })
        
        return jsonify({
            'reserved': False,
            'message': '座席情報が見つかりません'
        })
    
    except Exception as e:
        logger.error(f"Error getting seat info: {e}")
        return jsonify({
            'success': False,
            'message': '座席情報の取得中にエラーが発生しました'
        }), 500

@bp.route('/api/reserve', methods=['POST'])
@require_permission('reservation', 'write')
def create_reservation():
    """管理者用：予約を作成するAPI"""
    try:
        from flask import session
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'リクエストデータが不正です'}), 400
        
        bus_id = data.get('bus_id')
        seat_numbers = data.get('seat_numbers', [])
        
        if not bus_id or not seat_numbers:
            return jsonify({'success': False, 'message': '必須パラメータが不足しています'}), 400
        
        # セッションから管理者のユーザーIDを取得
        admin_username = session.get('username')
        if not admin_username:
            return jsonify({'success': False, 'message': 'セッション情報が取得できません'}), 401
        
        # 管理者として予約（user_idに "admin_" プレフィックスを付与）
        user_id = f"admin_{admin_username}"
        
        # Student サービスのAPIを使用して予約を作成
        result = admin_api.create_reservations(bus_id, seat_numbers, user_id)
        
        if result.get('success'):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error creating reservation: {e}")
        return jsonify({
            'success': False,
            'message': '予約作成中にエラーが発生しました'
        }), 500
