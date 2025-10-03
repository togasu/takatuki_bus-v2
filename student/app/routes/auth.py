from flask import Blueprint, render_template, request, redirect, url_for, make_response
from markupsafe import escape
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import os
from datetime import datetime
from ..utils.auth_utils import user_password_exist, add_token_str, check_session
from ..utils.user_utils import check_user_registration

auth_bp = Blueprint('auth', __name__)

# Rate limiter should be initialized in the main app
limiter = None

def init_limiter(app):
    global limiter
    limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minutes"])

def add_security_headers(response):
    """セキュリティヘッダーを追加"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
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
        admin_host = os.getenv('ADMIN_SERVICE_HOST', 'admin')
        admin_port = os.getenv('ADMIN_SERVICE_PORT', '5000')
        admin_verify_url = f"http://{admin_host}:{admin_port}/api/auth/verify-admin"
        
        # JSONデータとして送信
        auth_data = {
            'username': username,
            'password': password
        }
        
        print(f"Attempting admin verification to: {admin_verify_url}")
        
        # adminサービスに認証リクエストを送信
        response = requests.post(
            admin_verify_url,
            json=auth_data,
            timeout=5,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Student-Service-Auth'
            }
        )
        
        print(f"Admin verification response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"Admin verification response: {json_response}")
                
                # adminユーザーかどうかをチェック
                if json_response.get('is_admin'):
                    return {
                        'user_id': json_response.get('user_id'),
                        'username': json_response.get('username'),
                        'role': json_response.get('role'),
                        'email': json_response.get('email')
                    }
            except Exception as e:
                print(f"Failed to parse admin verification response: {e}")
        
        return None
            
    except requests.exceptions.RequestException as e:
        print(f"Admin verification service error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in admin verification: {e}")
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
        admin_host = os.getenv('ADMIN_SERVICE_HOST', 'admin')
        admin_port = os.getenv('ADMIN_SERVICE_PORT', '5000')
        admin_auth_url = f"http://{admin_host}:{admin_port}/api/auth/login"
        
        # JSONデータとして送信
        auth_data = {
            'username': username,
            'password': password
        }
        
        print(f"Attempting admin authentication to: {admin_auth_url}")
        
        # adminサービスに認証リクエストを送信
        response = requests.post(
            admin_auth_url,
            json=auth_data,
            timeout=5,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Student-Service-Auth'
            }
        )
        
        print(f"Admin auth response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"Admin auth response: {json_response}")
                
                # APIレスポンスからトークンを取得
                if 'token' in json_response:
                    return {
                        'session_token': json_response['token'],
                        'user_id': json_response.get('user_id'),
                        'username': json_response.get('username'),
                        'role': json_response.get('role')
                    }
            except Exception as e:
                print(f"Failed to parse admin auth response: {e}")
        
        return None
            
    except requests.exceptions.RequestException as e:
        print(f"Admin session creation service error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in admin session creation: {e}")
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
        driver_host = os.getenv('DRIVER_SERVICE_HOST', 'driver')
        driver_port = os.getenv('DRIVER_SERVICE_PORT', '5001')
        
        # driverサービスはフォーム形式でのログインを想定
        auth_data = {
            'username': username,
            'password': password
        }
        
        print(f"Attempting driver authentication to driver service")
        
        # driverサービスのログイン処理を呼び出し
        # 実際にはdriverサービスのセッションマネージャーを使用する必要がある
        # ここではドライバー認証の基本的なチェックのみ実装
        
        # ドライバーかどうかをユーザー名で判定（簡易的な実装）
        if username.startswith('driver'):
            return {
                'session_token': f"driver_{username}_{datetime.now().timestamp()}",
                'username': username,
                'role': 'driver'
            }
        
        return None
            
    except Exception as e:
        print(f"Unexpected error in driver session creation: {e}")
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
    print(f'username={escape(username)}')
    password = request.form.get('password', '')
    
    # ユーザー名とパスワードの基本チェック
    if not username or not password:
        response = make_response(render_template('top.html', message="ユーザー名とパスワードを入力してください。"))
        return add_security_headers(response)
    
    # 入力値のサニタイズ（基本的な文字数制限とパターンチェック）
    if len(username) > 50 or len(password) > 100:
        response = make_response(render_template('top.html', message="入力値が長すぎます。"))
        return add_security_headers(response)
    
    # 危険な文字のチェック
    if any(char in username for char in ['<', '>', '"', "'", '&', '\n', '\r', '\t']):
        response = make_response(render_template('top.html', message="無効な文字が含まれています。"))
        return add_security_headers(response)
    
    API_URL = "http://192.168.100.5:49155"  # TODO: 設定ファイルから読み込み
    REGIST_API = "http://192.168.100.5:49160"
    
    # adminアカウントのチェック（adminサービスにリダイレクト）
    admin_session = create_admin_session(username, password)
    if admin_session:
        print(f"Admin credentials verified and session created for user: {username}")
        # adminセッション作成成功時、Cookieを設定してadminダッシュボードにリダイレクト
        try:
            print("Admin session created successfully")
            response = make_response(redirect("https://localhost/admin/"))
            
            # セッショントークンをCookieに設定
            response.set_cookie(
                'admin_session_token', 
                admin_session['session_token'],
                max_age=3600,  # 1時間
                httponly=True,
                secure=True,
                domain='localhost',  # ドメイン間でCookieを共有
                path='/admin'  # adminパス専用
            )
            print(f"Admin session cookie set: {admin_session['session_token']}")
            return add_security_headers(response)
        except Exception as e:
            print(f"Admin session cookie setting error: {e}")
            # フォールバック: 直接リダイレクト（セッションなし）
            response = make_response(redirect("https://localhost/admin/login"))
            return add_security_headers(response)
    
    # driverアカウントのチェック
    driver_session = create_driver_session(username, password)
    if driver_session:
        print(f"Driver credentials verified and session created for user: {username}")
        # driverセッション作成成功時、Cookieを設定してdriverトップページにリダイレクト
        try:
            print("Driver session created successfully")
            response = make_response(redirect("https://localhost/driver/"))
            
            # セッショントークンをCookieに設定
            response.set_cookie(
                'driver_session_token', 
                driver_session['session_token'],
                max_age=3600,  # 1時間
                httponly=True,
                secure=True,
                domain='localhost',  # ドメイン間でCookieを共有
                path='/driver'  # driverパス専用
            )
            print(f"Driver session cookie set: {driver_session['session_token']}")
            return add_security_headers(response)
        except Exception as e:
            print(f"Driver session cookie setting error: {e}")
            # フォールバック: 直接リダイレクト（セッションなし）
            response = make_response(redirect("https://localhost/driver/login"))
            return add_security_headers(response)
    
    # 学生（k番号）のみ対応
    if username[0] != 'k':
        response = make_response(render_template('top.html', message="学生用システムです。k番号でログインしてください。"))
        return add_security_headers(response)
    
    # LDAP認証
    exist, student_id, user_full_name = user_password_exist(username, password)
    print(f'user_full_name={user_full_name}')

    if exist:
        # 内部でユーザー登録状況をチェック
        status_code, message = check_user_registration(student_id)
        print(f"User registration status: {status_code} - {message}")
        
        if status_code == 410:
            response = make_response(render_template('error.html', error_message=message))
            return add_security_headers(response)
        elif status_code == 405:
            response = make_response(render_template('error.html', error_message=message))
            return add_security_headers(response)
        
        session_str = add_token_str(username, student_id)
        print(f"Session token: {session_str}")
        
        if session_str is None:
            # Redis接続エラー等でセッション作成に失敗した場合
            response = make_response(render_template('error.html', error_message="システムエラーが発生しました。しばらく時間をおいてから再度お試しください。"))
            return add_security_headers(response)
        
        # 学生ログイン成功時、studentのpersonalページにリダイレクト
        response = make_response(redirect(url_for('main.personal')))
        response.set_cookie('token', session_str, max_age=900)
        response.set_cookie('user_full_name', user_full_name, max_age=900)
        print(f"Student login successful, redirecting to personal page for user: {escape(username)}")
        return add_security_headers(response)
    else:
        response = make_response(render_template('top.html', message="ログインに失敗しました"))
        return add_security_headers(response)

@auth_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """admin_dashboardからのアクセス専用エンドポイント"""
    print(f"=== ADMIN LOGIN ENDPOINT CALLED ===")
    print(f"Method: {request.method}")
    print(f"Referer: {request.headers.get('Referer', 'None')}")
    print(f"User-Agent: {request.headers.get('User-Agent', 'None')}")
    print(f"All cookies: {dict(request.cookies)}")
    print(f"Form data: {dict(request.form)}")
    
    # POSTリクエストの場合はフォームデータからトークンを取得
    if request.method == 'POST':
        admin_session_token = request.form.get('admin_token')
        print(f"Admin token from form: {admin_session_token}")
    else:
        # GETリクエストの場合はCookieからトークンを取得
        admin_session_token = request.cookies.get('admin_session_token')
        print(f"Admin session token from cookie: {admin_session_token}")
    
    if not admin_session_token:
        print("ERROR: No admin session token found")
        # adminセッションがない場合はログインページにリダイレクト
        return redirect("https://localhost/admin/login")
    
    print(f"Found admin token: {admin_session_token[:20]}...")
    
    # adminサービスでセッションを確認
    try:
        admin_host = os.getenv('ADMIN_SERVICE_HOST', 'admin')
        admin_port = os.getenv('ADMIN_SERVICE_PORT', '5000')
        admin_check_url = f"http://{admin_host}:{admin_port}/api/auth/check"
        
        print(f"Checking admin session at: {admin_check_url}")
        
        response = requests.get(
            admin_check_url,
            headers={
                'X-Service-Auth': admin_session_token,
                'User-Agent': 'Student-Service-Auth'
            },
            timeout=15  # タイムアウトを15秒に増加
        )
        
        print(f"Admin check response status: {response.status_code}")
        
        if response.status_code == 200:
            json_response = response.json()
            print(f"Admin check response: {json_response}")
            
            if json_response.get('status') == 'authenticated':
                user_data = json_response.get('user_data', {})
                
                # adminユーザー用のstudentサービスセッションを作成
                admin_info = {
                    'user_id': json_response.get('user_id'),
                    'username': user_data.get('username'),
                    'role': user_data.get('role'),
                    'email': user_data.get('email')
                }
                
                print(f"Creating student session for admin: {admin_info}")
                
                from ..utils.auth_utils import add_admin_token_str
                session_str = add_admin_token_str(user_data.get('username'), admin_info)
                
                if session_str:
                    # studentサービスにログイン成功
                    print(f"Student session created successfully: {session_str[:20]}...")
                    response = make_response(redirect(url_for('main.personal')))
                    response.set_cookie('token', session_str, max_age=900)
                    response.set_cookie('user_full_name', f"Admin {user_data.get('username')}", max_age=900)
                    print(f"Admin login to student service successful for user: {user_data.get('username')}")
                    return add_security_headers(response)
                else:
                    print("ERROR: Failed to create student session")
                    response = make_response(render_template('error.html', error_message="セッション作成に失敗しました。"))
                    return add_security_headers(response)
            else:
                print(f"ERROR: Admin session not authenticated: {json_response}")
        else:
            print(f"ERROR: Admin check failed with status {response.status_code}")
    
    except requests.exceptions.Timeout as e:
        print(f"ERROR: Admin service timeout: {e}")
        response = make_response(render_template('error.html', error_message="管理者サービスとの通信がタイムアウトしました。しばらく待ってから再度お試しください。"))
        return add_security_headers(response)
    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Admin service connection error: {e}")
        response = make_response(render_template('error.html', error_message="管理者サービスに接続できません。"))
        return add_security_headers(response)
    except Exception as e:
        print(f"ERROR: Admin session verification error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        response = make_response(render_template('error.html', error_message="システムエラーが発生しました。"))
        return add_security_headers(response)
        
    # 認証に失敗した場合はadminログインページにリダイレクト
    print("Admin authentication failed, redirecting to admin login")
    return redirect("https://localhost/admin/login")
