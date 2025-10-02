from flask import Blueprint, render_template, session, request, jsonify, redirect, url_for, flash, make_response
from app.utils.auth_utils import SessionManager, login_required, login_user, PasswordManager
from app.database import db
from app.utils.now_jst import now_jst

bp = Blueprint("index", __name__)
session_manager = SessionManager()

@bp.before_request
def log_request():
    """リクエストの詳細をログに記録"""
    print(f"Index Blueprint - Method: {request.method}, Path: {request.path}")
    print(f"Endpoint: {request.endpoint}")
    print(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}")

@bp.errorhandler(405)
def method_not_allowed(error):
    """405 Method Not Allowedエラーハンドラー"""
    print(f"405 Error in Index - Method: {request.method}, Path: {request.path}")
    return jsonify({
        "error": True,
        "error_type": "Method Not Allowed", 
        "message": "このメソッドは許可されていません",
        "status_code": 405,
        "request_method": request.method,
        "request_path": request.path
    }), 405

@bp.route("/login", methods=["GET", "POST", "OPTIONS"])
def login():
    """ログインページとログイン処理"""
    # OPTIONSリクエストの場合
    if request.method == "OPTIONS":
        response = jsonify({"methods": ["GET", "POST", "OPTIONS"]})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return response
    # デバッグ情報を出力
    print(f"Login route accessed: Method={request.method}, Endpoint={request.endpoint}")
    print(f"Request URL: {request.url}")
    print(f"Request path: {request.path}")
    print(f"Request headers: {dict(request.headers)}")
    
    if request.method == "GET":
        # 既にログイン済みの場合はダッシュボードにリダイレクト
        user_id = session.get('user_id')
        if user_id:
            from app.models.user import User
            user = User.query.get(user_id)
            if user and user.is_active:
                return redirect(url_for('index.index'))
        
        # Cookieベースのセッションもチェック
        session_token = request.cookies.get('admin_session_token')
        if session_token:
            session_data = session_manager.validate_session(session_token)
            if session_data:
                from app.models.user import User
                user = User.query.get(session_data['user_id'])
                if user and user.is_active:
                    session['user_id'] = user.id
                    return redirect(url_for('index.index'))
        
        return render_template("login.html")
    
    # POST処理 - ログイン認証
    print("Processing POST request for login")
    username = request.form.get('username')
    password = request.form.get('password')
    print(f"Username: {username}, Password: {'*' * len(password) if password else 'None'}")
    
    if not username or not password:
        flash('ユーザー名とパスワードを入力してください', 'error')
        return render_template("login.html")
    
    # ユーザー認証
    from app.models.user import User
    user = User.query.filter_by(username=username, is_active=True).first()
    
    if user and user.check_password(password):
        # ログイン成功
        session_token = login_user(user, remember=True)
        
        # ログイン時刻を更新
        user.last_login = now_jst()
        db.session.commit()
        
        # レスポンスを作成
        response = make_response(redirect(url_for('index.index')))
        
        # セッショントークンをCookieに設定
        if session_token:
            response.set_cookie(
                'admin_session_token', 
                session_token,
                max_age=3600,  # 1時間
                httponly=True,
                secure=True,
                samesite='Strict'
            )
        
        flash('ログインしました', 'success')
        return response
    else:
        # ログイン失敗
        flash('ユーザー名またはパスワードが間違っています', 'error')
        return render_template("login.html")

@bp.route("/debug/routes", methods=["GET"])
def debug_routes():
    """デバッグ用：全ルートを表示"""
    from flask import current_app
    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "rule": rule.rule,
            "methods": list(rule.methods)
        })
    return jsonify({
        "total_routes": len(routes),
        "routes": routes
    })

@bp.route("/", methods=["GET"])
def index():
    """管理者ダッシュボード"""
    print(f"Admin index route accessed")
    print(f"All cookies: {dict(request.cookies)}")
    print(f"Session data: {dict(session)}")
    
    # Cookieベースのセッションチェック
    session_token = request.cookies.get('admin_session_token')
    print(f"Checking session token from cookie: {session_token}")
    
    if session_token:
        session_data = session_manager.validate_session(session_token)
        print(f"Session validation result: {session_data}")
        
        if session_data:
            from app.models.user import User
            user = User.query.get(session_data['user_id'])
            if user and user.is_active:
                # セッションに情報を設定
                session['user_id'] = user.id
                session['username'] = user.username
                print(f"User authenticated: {user.username}")
                
                # APIリクエストの場合はJSONレスポンスを返す
                if request.headers.get('Content-Type') == 'application/json' or request.headers.get('Accept') == 'application/json':
                    return {
                        "service": "Admin",
                        "message": "HTTP route works!",
                        "user": user.username
                    }
                
                # ブラウザからのアクセスの場合は管理画面を表示
                return render_template("admin_dashboard.html", user=user)
    
    # 通常のセッションベースの認証もチェック
    user_id = session.get('user_id')
    if user_id:
        from app.models.user import User
        user = User.query.get(user_id)
        if user and user.is_active:
            print(f"User authenticated via session: {user.username}")
            # APIリクエストの場合はJSONレスポンスを返す
            if request.headers.get('Content-Type') == 'application/json' or request.headers.get('Accept') == 'application/json':
                return {
                    "service": "Admin", 
                    "message": "HTTP route works!",
                    "user": user.username
                }
            
            # ブラウザからのアクセスの場合は管理画面を表示
            return render_template("admin_dashboard.html", user=user)
    
    # 認証されていない場合はログインページにリダイレクト
    print("User not authenticated, redirecting to login")
    return redirect(url_for('index.login'))

@bp.route("/logout", methods=["GET", "POST"])
def logout():
    """ログアウト処理"""
    from app.utils.auth_utils import logout_user, create_logout_response
    from app.models.user import User
    
    # 現在のユーザー情報を取得（ログ記録用）
    current_user = None
    username = "不明"
    user_id = session.get('user_id')
    
    try:
        if user_id:
            current_user = User.query.get(user_id)
            if current_user:
                username = current_user.username
    except Exception as e:
        print(f"Error getting current user: {e}")
    
    # Cookieからのトークンも取得
    session_token = request.cookies.get('admin_session_token')
    
    # ログアウト処理の詳細ログ
    print(f"Logout process started for user_id: {user_id}")
    print(f"Session token from cookie: {session_token}")
    
    # 1. Redisからセッショントークンを削除
    tokens_deleted = []
    if session_token:
        try:
            session_manager.delete_session(session_token)
            tokens_deleted.append(session_token)
            print(f"Redis session token deleted: {session_token}")
        except Exception as e:
            print(f"Error deleting Redis session: {e}")
    
    # 2. ユーティリティ関数でログアウト処理（追加のトークンがあれば削除）
    try:
        cookie_token = logout_user()
        if cookie_token and cookie_token not in tokens_deleted:
            session_manager.delete_session(cookie_token)
            tokens_deleted.append(cookie_token)
            print(f"Additional token deleted: {cookie_token}")
    except Exception as e:
        print(f"Error in logout_user utility: {e}")
    
    # 3. ユーザーのログアウト時刻を記録
    if current_user:
        try:
            current_user.last_logout = now_jst()
            db.session.commit()
            print(f"Logout time recorded for user: {current_user.username}")
        except Exception as e:
            print(f"Error recording logout time: {e}")
            db.session.rollback()
    
    # 4. Flaskセッションをクリア
    session.clear()
    print("Flask session cleared")
    
    # 5. GETリクエストの場合は専用ログアウトページを表示
    if request.method == 'GET':
        # ログアウト専用ページを表示
        try:
            response = make_response(render_template(
                "logout.html", 
                logout_time=now_jst().strftime('%Y年%m月%d日 %H:%M:%S'),
                tokens_deleted_count=len(tokens_deleted),
                username=username
            ))
            
            # Cookieを削除
            response.set_cookie(
                'admin_session_token',
                '',
                expires=0,
                httponly=True,
                secure=True,
                samesite='Strict'
            )
            
            return response
        except Exception as e:
            print(f"Error rendering logout template: {e}")
            # テンプレートエラーの場合は簡単なメッセージを返す
            return f"""
            <html>
            <head><title>ログアウト完了</title></head>
            <body>
                <h1>{username}さん、お疲れさまでした</h1>
                <p>正常にログアウトしました。</p>
                <p>ログアウト時刻: {now_jst().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
                <a href="{url_for('index.login')}">再ログイン</a>
            </body>
            </html>
            """, 200
    
    # 6. POSTリクエストの場合は従来通りリダイレクト
    else:
        try:
            response = create_logout_response("https://localhost/")
            return response
        except Exception as e:
            print(f"Error creating logout response: {e}")
            return redirect(url_for('index.login'))
