from flask import Blueprint, render_template, request, jsonify
from app.database import get_db_connection
from app.authorization import require_permission
from datetime import datetime
import psycopg2.extras

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
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 予約情報を取得（バス情報も含む）
        query = """
            SELECT 
                r.id as reservation_id,
                r.seat_number,
                r.bus_id,
                r.user_id,
                r.approved,
                r.reserved_time,
                b.departure_time,
                b.arrival_time,
                b.status as bus_status,
                b.seats as total_seats,
                b.route_name,
                b.departure_location,
                b.arrival_location
            FROM "Reservation" r
            JOIN bus b ON r.bus_id = b.id
            WHERE r.user_id = %s
            ORDER BY b.departure_time DESC
        """
        
        cursor.execute(query, (student_id,))
        reservations = cursor.fetchall()
        
        cursor.close()
        
        return render_template('reservations/search.html', 
                             reservations=reservations, 
                             student_id=student_id)
    
    except Exception as e:
        print(f"Error searching reservations: {e}")
        import traceback
        traceback.print_exc()
        error_message = "予約データの検索中にエラーが発生しました。"
        if "does not exist" in str(e):
            error_message = "予約データベースが正しく設定されていません。システム管理者にお問い合わせください。"
        elif "connection" in str(e).lower():
            error_message = "データベースに接続できませんでした。しばらくしてから再度お試しください。"
        return render_template('reservations/search.html', 
                             error=error_message)
    finally:
        conn.close()

@bp.route('/bus/<int:bus_id>', methods=['GET'])
@require_permission('reservation', 'read')
def view_bus(bus_id):
    """便ごとの座席予約状況を表示"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # バス情報を取得
        cursor.execute("""
            SELECT *
            FROM bus
            WHERE id = %s
        """, (bus_id,))
        bus = cursor.fetchone()
        
        if not bus:
            return render_template('reservations/bus_view.html', 
                                 error="バスが見つかりませんでした")
        
        # 予約情報を取得
        cursor.execute("""
            SELECT seat_number, user_id, approved, reserved_time
            FROM "Reservation"
            WHERE bus_id = %s
            ORDER BY seat_number
        """, (bus_id,))
        reservations = cursor.fetchall()
        
        cursor.close()
        
        # 座席ごとの予約状態を作成（27席分）
        seat_status = []
        reservation_map = {r['seat_number']: r for r in reservations}
        
        for i in range(1, 28):  # 1〜27番の座席
            if i in reservation_map:
                reservation = reservation_map[i]
                seat_status.append({
                    'number': i,
                    'reserved': True,
                    'user_id': reservation['user_id'],
                    'approved': reservation['approved'],
                    'reserved_time': reservation['reserved_time']
                })
            else:
                seat_status.append({
                    'number': i,
                    'reserved': False,
                    'user_id': None,
                    'approved': None,
                    'reserved_time': None
                })
        
        return render_template('reservations/bus_view.html', 
                             bus=bus, 
                             seat_status=seat_status)
    
    except Exception as e:
        print(f"Error viewing bus reservations: {e}")
        import traceback
        traceback.print_exc()
        error_message = "バス予約情報の取得中にエラーが発生しました。"
        if "does not exist" in str(e):
            error_message = "予約データベースが正しく設定されていません。システム管理者にお問い合わせください。"
        elif "connection" in str(e).lower():
            error_message = "データベースに接続できませんでした。しばらくしてから再度お試しください。"
        return render_template('reservations/bus_view.html', 
                             error=error_message)
    finally:
        conn.close()

@bp.route('/bus/list', methods=['GET'])
@require_permission('reservation', 'read')
def bus_list():
    """予約があるバス一覧を表示"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 予約があるバスのみを取得
        query = """
            SELECT 
                b.id,
                b.departure_time,
                b.arrival_time,
                b.status,
                b.seats as total_seats,
                b.route_name,
                b.departure_location,
                b.arrival_location,
                COUNT(r.id) as reservation_count
            FROM bus b
            LEFT JOIN "Reservation" r ON b.id = r.bus_id
            GROUP BY b.id
            HAVING COUNT(r.id) > 0
            ORDER BY b.departure_time DESC
            LIMIT 100
        """
        
        cursor.execute(query)
        buses = cursor.fetchall()
        
        cursor.close()
        
        return render_template('reservations/bus_list.html', buses=buses)
    
    except Exception as e:
        print(f"Error listing buses: {e}")
        import traceback
        traceback.print_exc()
        error_message = "バス一覧の取得中にエラーが発生しました。"
        if "does not exist" in str(e):
            error_message = "予約データベースが正しく設定されていません。システム管理者にお問い合わせください。"
        elif "connection" in str(e).lower():
            error_message = "データベースに接続できませんでした。しばらくしてから再度お試しください。"
        return render_template('reservations/bus_list.html', 
                             error=error_message)
    finally:
        conn.close()
