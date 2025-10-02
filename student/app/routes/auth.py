from flask import Blueprint, render_template, request, redirect, url_for, make_response
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

@auth_bp.route('/')
def top():
    return render_template('top.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # GETリクエストの場合はログインページを表示
        return render_template('top.html')
    
    # POSTリクエストの場合は認証処理
    if limiter:
        limiter.limit("5 per 10 minute")(lambda: None)()
    
    username = request.form.get('username')
    print(f'username={username}')
    password = request.form.get('password')
    
    # ユーザー名とパスワードの基本チェック
    if not username or not password:
        return render_template('top.html', message="ユーザー名とパスワードを入力してください。")
    
    API_URL = "http://192.168.100.5:49155"  # TODO: 設定ファイルから読み込み
    REGIST_API = "http://192.168.100.5:49160"
    
    # adminアカウントのチェック
    admin_session = create_admin_session(username, password)
    if admin_session:
        print(f"Admin credentials verified and session created for user: {username}")
        # adminセッション作成成功時、Cookieを設定してリダイレクト
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
            return response
        except Exception as e:
            print(f"Admin session cookie setting error: {e}")
            # フォールバック: 直接リダイレクト（セッションなし）
            return redirect("https://localhost/admin/login")
    
    # 学生（k番号）のみ対応
    if username[0] != 'k':
        return render_template('top.html', message="学生用システムです。k番号でログインしてください。")
    
    # LDAP認証
    exist, student_id, user_full_name = user_password_exist(username, password)
    print(f'user_full_name={user_full_name}')

    if exist:
        # 内部でユーザー登録状況をチェック
        status_code, message = check_user_registration(student_id)
        print(f"User registration status: {status_code} - {message}")
        
        if status_code == 410:
            return render_template('error.html', error_message=message)
        elif status_code == 405:
            return render_template('error.html', error_message=message)
        
        session_str = add_token_str(username, student_id)
        print(f"Session token: {session_str}")
        
        if session_str is None:
            # Redis接続エラー等でセッション作成に失敗した場合
            return render_template('error.html', error_message="システムエラーが発生しました。しばらく時間をおいてから再度お試しください。")
        
        response = make_response(redirect(url_for('main.personal')))
        response.set_cookie('token', session_str, max_age=900)
        response.set_cookie('user_full_name', user_full_name, max_age=900)
        return response
    else:
        return render_template('top.html', message="ログインに失敗しました")
