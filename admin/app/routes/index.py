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
def root_redirect():
    """ルートアクセス時の処理"""
    # 管理者ログインページにリダイレクト
    return redirect(url_for('index.login'))

@bp.route("/", methods=["GET"])
@login_required
def index():
    """管理者ダッシュボード"""
    # APIリクエストの場合はJSONレスポンスを返す
    if request.headers.get('Content-Type') == 'application/json' or request.headers.get('Accept') == 'application/json':
        return {
            "service": "Admin",
            "message": "HTTP route works!"
        }
    
    # ブラウザからのアクセスの場合は管理画面を表示
    return render_template("admin_dashboard.html")

@bp.route("/logout", methods=["GET", "POST"])
def logout():
    """ログアウト処理"""
    from app.utils.auth_utils import logout_user, create_logout_response
    
    # ユーティリティ関数でログアウト処理
    cookie_token = logout_user()
    
    # セッションマネージャーからもトークンを削除
    if cookie_token:
        session_manager.delete_session(cookie_token)
    
    # セッションをクリア
    session.clear()
    
    # Cookieを削除してリダイレクト
    return create_logout_response("https://localhost/")
