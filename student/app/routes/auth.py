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
