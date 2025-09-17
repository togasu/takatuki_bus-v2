from flask import Blueprint, render_template, request, redirect, url_for, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from datetime import datetime
from ..utils.auth_utils import user_password_exist, add_token_str, check_session
from ..utils.user_utils import check_user_registration

auth_bp = Blueprint('auth', __name__)

# Rate limiter should be initialized in the main app
limiter = None

def init_limiter(app):
    global limiter
    limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minutes"])

@auth_bp.route('/')
def top():
    return render_template('top.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    if limiter:
        limiter.limit("5 per 10 minute")(lambda: None)()
    
    username = request.form.get('username')
    print(f'k_number={username}')
    password = request.form.get('password')
    
    API_URL = "http://192.168.100.5:49155"  # TODO: 設定ファイルから読み込み
    REGIST_API = "http://192.168.100.5:49160"
    
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
