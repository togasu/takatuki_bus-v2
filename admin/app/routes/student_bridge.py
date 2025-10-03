from flask import Blueprint, request, redirect, session, make_response, url_for
from app.utils.auth_utils import SessionManager
import os
import secrets
import time

bp = Blueprint("student_bridge", __name__)

# セッションマネージャーのインスタンス
session_manager = SessionManager()

@bp.route("/student-login", methods=["GET"])
def student_login():
    """adminダッシュボードから学生サービスへのブリッジ"""
    print("=== ADMIN TO STUDENT BRIDGE CALLED ===")
    
    # Flask sessionからユーザー情報を取得
    user_id = session.get('user_id')
    username = session.get('username')
    
    print(f"Session user_id: {user_id}")
    print(f"Session username: {username}")
    
    if not user_id or not username:
        print("No valid admin session found")
        return redirect("/admin/login")
    
    # Cookieからセッショントークンを取得
    admin_session_token = request.cookies.get('admin_session_token')
    
    if not admin_session_token:
        print("No admin session token in cookies")
        return redirect("/admin/login")
    
    print(f"Found admin token: {admin_session_token[:20]}...")
    
    # 一時的な認証トークンを生成（時間制限付き）
    temp_token = secrets.token_hex(32)
    timestamp = str(int(time.time()))
    
    # studentサービスにGETパラメータで認証情報を渡す
    student_url = f"https://localhost/student/admin-login"
    
    print(f"Redirecting to student service: {student_url}")
    
    # POSTフォームでstudentサービスに転送
    html_form = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>学生サービスに移動中...</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background-color: #f5f5f5;
            }}
            .container {{
                text-align: center;
                background: white;
                padding: 2rem;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 1rem auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="spinner"></div>
            <h3>学生サービスに移動中...</h3>
            <p>しばらくお待ちください</p>
            <form id="redirectForm" action="{student_url}" method="POST">
                <input type="hidden" name="admin_token" value="{admin_session_token}">
                <input type="hidden" name="temp_token" value="{temp_token}">
                <input type="hidden" name="timestamp" value="{timestamp}">
                <input type="hidden" name="username" value="{username}">
            </form>
        </div>
        <script>
            // 自動的にフォームを送信
            setTimeout(function() {{
                document.getElementById('redirectForm').submit();
            }}, 1000);
        </script>
    </body>
    </html>
    """
    
    return html_form