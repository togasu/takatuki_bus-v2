from flask import Blueprint, render_template, request, redirect, url_for, make_response
from markupsafe import escape
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import re
import logging
from datetime import datetime
from ..utils.auth_utils import user_password_exist, add_token_str, check_session
from ..utils.user_utils import check_user_registration
from .. import config

# ロギング設定
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Rate limiter should be initialized in the main app
limiter = None

def init_limiter(app):
    global limiter
    limiter = Limiter(
        get_remote_address, 
        app=app, 
        default_limits=["100 per minute"],
        storage_uri=config.RATELIMIT_STORAGE_URL
    )

def add_security_headers(response):
    """セキュリティヘッダーを追加"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    return response

def verify_admin_user(username, password):
    """adminサービスでadminユーザーかどうかを確認
    
    Args:
        username (str): ユーザー名
        password (str): パスワード
    
    Returns:
        dict: adminユーザー情報またはNone
    """
    try:
        # adminサービスの認証APIエンドポイント
        admin_verify_url = f"http://{config.ADMIN_SERVICE_HOST}:{config.ADMIN_SERVICE_PORT}/api/auth/verify-admin"
        
        # JSONデータとして送信
        auth_data = {
            'username': username,
            'password': password
        }
        
        logger.info(f"Attempting admin verification for user: {username}")
        
        # adminサービスに認証リクエストを送信
        response = requests.post(
            admin_verify_url,
            json=auth_data,
            timeout=config.REQUEST_TIMEOUT,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Student-Service-Auth'
            }
        )
        
        logger.info(f"Admin verification response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                
                # adminユーザーかどうかをチェック
                if json_response.get('is_admin'):
                    logger.info(f"Admin user verified: {username}")
                    return {
                        'user_id': json_response.get('user_id'),
                        'username': json_response.get('username'),
                        'role': json_response.get('role'),
                        'email': json_response.get('email')
                    }
            except Exception as e:
                logger.error(f"Failed to parse admin verification response: {type(e).__name__}")
        
        return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Admin verification service error: {type(e).__name__}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in admin verification: {type(e).__name__}")
        return None

def create_admin_session(username, password):
    """adminサービスでセッションを作成
    
    Args:
        username (str): 管理者ユーザー名
        password (str): 管理者パスワード
    
    Returns:
        dict: セッション情報（session_tokenを含む）またはNone
    """
    try:
        # adminサービスの認証APIエンドポイント（直接セッション作成）
        admin_auth_url = f"http://{config.ADMIN_SERVICE_HOST}:{config.ADMIN_SERVICE_PORT}/api/auth/login"
        
        # JSONデータとして送信
        auth_data = {
            'username': username,
            'password': password
        }
        
        logger.info(f"Attempting admin authentication for user: {username}")
        
        # adminサービスに認証リクエストを送信
        response = requests.post(
            admin_auth_url,
            json=auth_data,
            timeout=config.REQUEST_TIMEOUT,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Student-Service-Auth'
            }
        )
        
        logger.info(f"Admin auth response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                
                # APIレスポンスからトークンを取得
                if 'token' in json_response:
                    logger.info(f"Admin session created for user: {username}")
                    return {
                        'session_token': json_response['token'],
                        'user_id': json_response.get('user_id'),
                        'username': json_response.get('username'),
                        'role': json_response.get('role')
                    }
            except Exception as e:
                logger.error(f"Failed to parse admin auth response: {type(e).__name__}")
        
        logger.warning(f"Admin authentication failed for user: {username}")
        return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Admin session creation service error: {type(e).__name__}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in admin session creation: {type(e).__name__}")
        return None

def create_driver_session(username, password):
    """driverサービスでセッションを作成
    
    Args:
        username (str): ドライバーユーザー名
        password (str): ドライバーパスワード
    
    Returns:
        dict: セッション情報（session_tokenを含む）またはNone
    """
    try:
        # driverサービスの認証APIエンドポイント
        driver_auth_url = f"http://{config.DRIVER_SERVICE_HOST}:{config.DRIVER_SERVICE_PORT}/api/auth/login"
        
        # driverサービスはフォーム形式でのログインを想定
        auth_data = {
            'username': username,
            'password': password
        }
        
        logger.info(f"Attempting driver authentication for user: {username}")
        
        # driverサービスのログイン処理を呼び出し
        # 実際にはdriverサービスのセッションマネージャーを使用する必要がある
        # ここではドライバー認証の基本的なチェックのみ実装
        
        # ドライバーかどうかをユーザー名で判定（簡易的な実装）
        if username.startswith('driver'):
            logger.info(f"Driver session created for user: {username}")
            return {
                'session_token': f"driver_{username}_{datetime.now().timestamp()}",
                'username': username,
                'role': 'driver'
            }
        
        return None
            
    except Exception as e:
        logger.error(f"Unexpected error in driver session creation: {type(e).__name__}")
        return None

@auth_bp.route('/')
def top():
    """トップページ - ログイン画面を表示"""
    response = make_response(render_template('top.html'))
    return add_security_headers(response)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # GETリクエストの場合はログインページを表示
        response = make_response(render_template('top.html'))
        return add_security_headers(response)
    
    # POSTリクエストの場合は認証処理
    if limiter:
        limiter.limit("5 per 10 minute")(lambda: None)()
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    # ユーザー名のみログに出力（パスワードは絶対に出力しない）
    logger.info(f'Login attempt for username: {escape(username)}')
    
    # ユーザー名とパスワードの基本チェック
    if not username or not password:
        response = make_response(render_template('top.html', message="ユーザー名とパスワードを入力してください。"))
        return add_security_headers(response)
    
    # 入力値のサニタイズ（基本的な文字数制限とパターンチェック）
    if len(username) > 50 or len(password) > 100:
        response = make_response(render_template('top.html', message="入力値が無効です。"))
        return add_security_headers(response)
    
    # より厳格な文字チェック（英数字、アンダースコア、ハイフン、ドット、@のみ許可）
    if not re.match(r'^[a-zA-Z0-9_\-\.@]+$', username):
        logger.warning(f'Invalid characters in username attempt: {username}')
        response = make_response(render_template('top.html', message="無効な文字が含まれています。"))
        return add_security_headers(response)
    
    # adminアカウントのチェック（adminサービスにリダイレクト）
    admin_session = create_admin_session(username, password)
    if admin_session:
        logger.info(f"Admin credentials verified and session created for user: {username}")
        # adminセッション作成成功時、Cookieを設定してadminダッシュボードにリダイレクト
        try:
            logger.info("Admin session created successfully")
            response = make_response(redirect("https://localhost/admin/"))
            
            # セッショントークンをCookieに設定（SameSite属性を追加）
            response.set_cookie(
                'admin_session_token', 
                admin_session['session_token'],
                max_age=3600,  # 1時間
                httponly=True,
                secure=True,
                samesite='Strict',  # CSRF対策
                domain=config.COOKIE_DOMAIN,
                path='/admin'  # adminパス専用
            )
            logger.info("Admin session cookie set successfully")
            return add_security_headers(response)
        except Exception as e:
            logger.error(f"Admin session cookie setting error: {type(e).__name__}")
            # フォールバック: 直接リダイレクト（セッションなし）
            response = make_response(redirect("https://localhost/admin/login"))
            return add_security_headers(response)
    
    # driverアカウントのチェック
    driver_session = create_driver_session(username, password)
    if driver_session:
        logger.info(f"Driver credentials verified and session created for user: {username}")
        # driverセッション作成成功時、Cookieを設定してdriverトップページにリダイレクト
        try:
            logger.info("Driver session created successfully")
            response = make_response(redirect("https://localhost/driver/"))
            
            # セッショントークンをCookieに設定（SameSite属性を追加）
            response.set_cookie(
                'driver_session_token', 
                driver_session['session_token'],
                max_age=3600,  # 1時間
                httponly=True,
                secure=True,
                samesite='Strict',  # CSRF対策
                domain=config.COOKIE_DOMAIN,
                path='/driver'  # driverパス専用
            )
            logger.info("Driver session cookie set successfully")
            return add_security_headers(response)
        except Exception as e:
            logger.error(f"Driver session cookie setting error: {type(e).__name__}")
            # フォールバック: 直接リダイレクト（セッションなし）
            response = make_response(redirect("https://localhost/driver/login"))
            return add_security_headers(response)
    
    # LDAP認証
    exist, student_id, user_full_name = user_password_exist(username, password)
    logger.info(f'LDAP authentication result for {username}: {exist}')

    if exist:
        # 内部でユーザー登録状況をチェック
        status_code, message = check_user_registration(student_id)
        logger.info(f"User registration status for {student_id}: {status_code}")
        
        if status_code == 410:
            response = make_response(render_template('error.html', error_message=message))
            return add_security_headers(response)
        elif status_code == 405:
            response = make_response(render_template('error.html', error_message=message))
            return add_security_headers(response)
        
        session_str = add_token_str(username, student_id)
        
        if session_str is None:
            # Redis接続エラー等でセッション作成に失敗した場合
            logger.error(f"Failed to create session for user: {username}")
            response = make_response(render_template('error.html', error_message="システムエラーが発生しました。しばらく時間をおいてから再度お試しください。"))
            return add_security_headers(response)
        
        # 学生ログイン成功時、studentのpersonalページにリダイレクト
        response = make_response(redirect(url_for('main.personal')))
        response.set_cookie('token', session_str, max_age=900, httponly=True, secure=True, samesite='Strict')
        response.set_cookie('user_full_name', user_full_name, max_age=900, httponly=True, secure=True, samesite='Strict')
        logger.info(f"Student login successful for user: {escape(username)}")
        return add_security_headers(response)
    else:
        logger.warning(f"Login failed for user: {username}")
        response = make_response(render_template('top.html', message="ログインに失敗しました"))
        return add_security_headers(response)

@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """admin_dashboardからのアクセス専用エンドポイント"""
    logger.info("Admin login endpoint called")
    logger.info(f"Method: {request.method}")
    
    # POSTリクエストの場合はフォームデータからトークンを取得
    if request.method == 'POST':
        admin_session_token = request.form.get('admin_token')
        logger.info("Admin token received from form")
    else:
        # GETリクエストの場合はCookieからトークンを取得
        admin_session_token = request.cookies.get('admin_session_token')
        logger.info("Admin token received from cookie")
    
    if not admin_session_token:
        logger.warning("No admin session token found")
        # adminセッションがない場合はログインページにリダイレクト
        return redirect("https://localhost/admin/login")
    
    logger.info("Admin token found, verifying session")
    
    # adminサービスでセッションを確認
    try:
        admin_check_url = f"http://{config.ADMIN_SERVICE_HOST}:{config.ADMIN_SERVICE_PORT}/api/auth/check"
        
        logger.info(f"Checking admin session at: {admin_check_url}")
        
        response = requests.get(
            admin_check_url,
            headers={
                'X-Service-Auth': admin_session_token,
                'User-Agent': 'Student-Service-Auth'
            },
            timeout=config.REQUEST_TIMEOUT
        )
        
        logger.info(f"Admin check response status: {response.status_code}")
        
        if response.status_code == 200:
            json_response = response.json()
            
            if json_response.get('status') == 'authenticated':
                user_data = json_response.get('user_data', {})
                
                # adminユーザー用のstudentサービスセッションを作成
                admin_info = {
                    'user_id': json_response.get('user_id'),
                    'username': user_data.get('username'),
                    'role': user_data.get('role'),
                    'email': user_data.get('email')
                }
                
                logger.info(f"Creating student session for admin user")
                
                from ..utils.auth_utils import add_admin_token_str
                session_str = add_admin_token_str(user_data.get('username'), admin_info)
                
                if session_str:
                    # studentサービスにログイン成功
                    logger.info(f"Student session created successfully")
                    response = make_response(redirect(url_for('main.personal')))
                    response.set_cookie('token', session_str, max_age=900, httponly=True, secure=True, samesite='Strict')
                    response.set_cookie('user_full_name', f"Admin {user_data.get('username')}", max_age=900, httponly=True, secure=True, samesite='Strict')
                    logger.info(f"Admin login to student service successful for user: {user_data.get('username')}")
                    return add_security_headers(response)
                else:
                    logger.error("Failed to create student session")
                    response = make_response(render_template('error.html', error_message="システムエラーが発生しました。"))
                    return add_security_headers(response)
            else:
                logger.warning("Admin session not authenticated")
        else:
            logger.warning(f"Admin check failed with status {response.status_code}")
    
    except requests.exceptions.Timeout:
        logger.error("Admin service timeout")
        response = make_response(render_template('error.html', error_message="システムエラーが発生しました。しばらく待ってから再度お試しください。"))
        return add_security_headers(response)
    except requests.exceptions.ConnectionError:
        logger.error("Admin service connection error")
        response = make_response(render_template('error.html', error_message="システムエラーが発生しました。"))
        return add_security_headers(response)
    except Exception as e:
        logger.error(f"Admin session verification error: {type(e).__name__}")
        response = make_response(render_template('error.html', error_message="システムエラーが発生しました。"))
        return add_security_headers(response)
        
    # 認証に失敗した場合はadminログインページにリダイレクト
    logger.warning("Admin authentication failed, redirecting to admin login")
    return redirect("https://localhost/admin/login")


# ========================================
# Auth System用エンドポイント
# ========================================

@auth_bp.route('/auth', methods=['GET'])
def nfc_auth():
    """
    バス車内認証システム用エンドポイント
    NFCカードのIDmで予約を検索し、座席番号を返す
    
    Request JSON:
        {
            "idm": "カードIDm（16進数文字列）",
            "number": バス号車番号（1-4）
        }
    
    Response:
        200: {"seat_number": 座席番号, "reservation_id": 予約ID}
        401: {"error": "Card not registered"}
        403: {"error": "Bus ID mismatch", "bus_number": 正しいバス号車}
        404: {"error": "No reservation found"}
        500: {"error": "Internal server error"}
    """
    from ..database import db
    from ..models.user import User
    from ..models.reservation import Reservation
    from ..models.bus import Bus
    from datetime import datetime, timedelta
    
    try:
        data = request.get_json()
        idm = data.get('idm')
        bus_number = data.get('number')
        
        if not idm or bus_number is None:
            return {'error': 'Missing required parameters'}, 400
        
        logger.info(f"NFC auth request: IDM={idm}, Bus={bus_number}")
        
        # IDmからユーザーを検索
        user = User.query.filter_by(idm_bus=idm).first()
        if not user:
            logger.warning(f"User not found for IDM: {idm}")
            return {'error': 'Card not registered'}, 401
        
        # 現在時刻から近い未来のバス便を検索（当日～翌日）
        now = datetime.now()
        future_time = now + timedelta(hours=24)
        
        # ユーザーの予約を検索
        reservation = Reservation.query.filter(
            Reservation.user_id == user.student_id,
            Reservation.approved == 0  # 未認証の予約のみ
        ).join(Bus).filter(
            Bus.busid == bus_number,
            Bus.departure_time >= now,
            Bus.departure_time <= future_time
        ).order_by(Bus.departure_time.asc()).first()
        
        if not reservation:
            logger.warning(f"No reservation found for user {user.student_id} on bus {bus_number}")
            
            # 別のバスに予約がないか確認
            other_reservation = Reservation.query.filter(
                Reservation.user_id == user.student_id,
                Reservation.approved == 0
            ).join(Bus).filter(
                Bus.departure_time >= now,
                Bus.departure_time <= future_time
            ).first()
            
            if other_reservation:
                correct_bus = Bus.query.get(other_reservation.bus_id)
                logger.info(f"User has reservation on different bus: {correct_bus.busid}")
                return {'error': 'Bus ID mismatch', 'bus_number': correct_bus.busid}, 403
            
            return {'error': 'No reservation found'}, 404
        
        logger.info(f"Reservation found: ID={reservation.id}, Seat={reservation.seat_number}")
        return {
            'seat_number': reservation.seat_number,
            'reservation_id': reservation.id,
            'user_id': user.student_id
        }, 200
        
    except Exception as e:
        logger.error(f"NFC auth error: {type(e).__name__}: {str(e)}")
        return {'error': 'Internal server error'}, 500


@auth_bp.route('/auth/approve', methods=['POST'])
def approve_reservation():
    """
    予約承認エンドポイント（auth_system専用）
    バス車内での認証完了後、予約をapproved=1に更新
    
    セキュリティ対策:
    - APIキー認証（X-Auth-System-Keyヘッダー必須）
    - 予約とバスの整合性チェック
    - 時間制限（バス出発時刻の前後1時間のみ）
    - 重複承認防止
    
    Request Headers:
        X-Auth-System-Key: auth_system専用APIキー
    
    Request JSON:
        {
            "reservation_id": 予約ID,
            "bus_number": バス号車番号
        }
    
    Response:
        200: {"success": true, "message": "Reservation approved"}
        400: {"error": "Missing required parameters"}
        401: {"error": "Unauthorized - Invalid API key"}
        403: {"error": "Already approved" | "Bus time window expired"}
        404: {"error": "Reservation not found"}
        409: {"error": "Bus number mismatch"}
        500: {"error": "Internal server error"}
    """
    from ..database import db
    from ..models.reservation import Reservation
    from ..models.bus import Bus
    from datetime import datetime, timedelta
    
    try:
        # APIキー認証
        api_key = request.headers.get('X-Auth-System-Key')
        if not api_key or api_key != config.AUTH_SYSTEM_API_KEY:
            logger.warning(f"Unauthorized approve attempt from {request.remote_addr}")
            return {'error': 'Unauthorized - Invalid API key'}, 401
        
        data = request.get_json()
        reservation_id = data.get('reservation_id')
        bus_number = data.get('bus_number')
        
        if not reservation_id or bus_number is None:
            return {'error': 'Missing required parameters'}, 400
        
        logger.info(f"Approve request: Reservation={reservation_id}, Bus={bus_number}")
        
        # 予約を検索（バス情報も取得）
        reservation = Reservation.query.join(Bus).filter(
            Reservation.id == reservation_id
        ).first()
        
        if not reservation:
            logger.warning(f"Reservation not found: {reservation_id}")
            return {'error': 'Reservation not found'}, 404
        
        # バス情報を取得
        bus = Bus.query.get(reservation.bus_id)
        if not bus:
            logger.error(f"Bus not found for reservation {reservation_id}")
            return {'error': 'Bus information not found'}, 404
        
        # バス号車の整合性チェック
        if bus.busid != bus_number:
            logger.warning(f"Bus number mismatch: expected {bus.busid}, got {bus_number}")
            return {'error': 'Bus number mismatch', 'expected': bus.busid}, 409
        
        # 時間制限チェック（バス出発時刻の前後1時間）
        now = datetime.now()
        time_window_start = bus.departure_time - timedelta(hours=1)
        time_window_end = bus.departure_time + timedelta(hours=1)
        
        if not (time_window_start <= now <= time_window_end):
            logger.warning(f"Approve attempt outside time window for reservation {reservation_id}")
            return {'error': 'Bus time window expired', 'departure_time': bus.departure_time.isoformat()}, 403
        
        # 重複承認防止
        if reservation.approved == 1:
            logger.info(f"Reservation {reservation_id} already approved")
            return {'error': 'Already approved', 'approved_at': reservation.reserved_time.isoformat() if reservation.reserved_time else None}, 403
        
        # 予約を承認済みに更新
        reservation.approved = 1
        reservation.reserved_time = now  # 承認時刻を記録
        db.session.commit()
        
        logger.info(f"Reservation {reservation_id} approved successfully by auth_system")
        return {
            'success': True, 
            'message': 'Reservation approved',
            'approved_at': now.isoformat(),
            'user_id': reservation.user_id,
            'seat_number': reservation.seat_number
        }, 200
        
    except Exception as e:
        logger.error(f"Approve reservation error: {type(e).__name__}: {str(e)}")
        db.session.rollback()
        return {'error': 'Internal server error'}, 500


@auth_bp.route('/auth/getbus', methods=['GET'])
def get_bus_for_auth():
    """
    auth_system用：次のバス便情報を取得
    
    Request JSON:
        {
            "number": バス号車番号（1-4）
        }
    
    Response:
        200: {
            "id": バスID,
            "departure_time": "出発時刻（YYYY/MM/DD HH:MM形式）",
            "ud": 上下区分（0:上り、1:下り）
        }
        404: {"error": "No bus found"}
    """
    from ..models.bus import Bus
    from datetime import datetime
    
    try:
        data = request.get_json()
        bus_number = data.get('number')
        
        if bus_number is None:
            return {'error': 'Missing bus number'}, 400
        
        # 現在時刻以降の最も近いバス便を検索
        now = datetime.now()
        bus = Bus.query.filter(
            Bus.busid == bus_number,
            Bus.departure_time >= now
        ).order_by(Bus.departure_time.asc()).first()
        
        if not bus:
            logger.warning(f"No upcoming bus found for bus number {bus_number}")
            return {'error': 'No bus found'}, 404
        
        return {
            'id': bus.busid,
            'departure_time': bus.departure_time.strftime('%Y/%m/%d %H:%M'),
            'ud': bus.ud
        }, 200
        
    except Exception as e:
        logger.error(f"Get bus error: {type(e).__name__}: {str(e)}")
        return {'error': 'Internal server error'}, 500

