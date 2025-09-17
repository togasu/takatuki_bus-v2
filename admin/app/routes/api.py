from flask import Blueprint, request, jsonify
from app.database import db
from datetime import datetime
from app.utils.now_jst import now_jst
from app.utils.auth_utils import SessionManager
from app.utils.decorators import safe_api_route, safe_route
from app.utils.error_handlers import create_error_response
import secrets
import os

bp = Blueprint("api", __name__, url_prefix="/api")

# セッションマネージャーのインスタンス
session_manager = SessionManager()

@bp.route("/auth/login", methods=["POST"])
@safe_api_route(required_fields=["username", "password"])
def auth_login():
    """管理者認証処理"""
    from app.models.user import User  # 遅延インポート
    
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    
    # ユーザー認証（実際のパスワード検証）
    user = User.query.filter_by(username=username, is_active=True).first()
    
    if user and user.check_password(password):
        # 認証成功時にRedisセッションを作成
        user_data = {
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
        
        session_token = session_manager.create_session(user.id, user_data)
        
        # ログイン時刻を更新
        user.last_login = now_jst()
        db.session.commit()
        
        return jsonify({
            "token": session_token,
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }), 200
    
    return create_error_response("認証に失敗しました", 401, "Authentication Failed")

@bp.route("/auth/check", methods=["GET"])
@safe_route
def auth_check():
    """認証状態確認"""
    auth_header = request.headers.get('X-Service-Auth')
    
    if not auth_header:
        return create_error_response("認証トークンがありません", 401, "No Auth Token")
    
    # Redisセッションから認証状態を確認
    session_data = session_manager.validate_session(auth_header)
    
    if session_data:
        return jsonify({
            "status": "authenticated",
            "user_id": session_data['user_id'],
            "user_data": session_data['user_data']
        }), 200
    
    return create_error_response("無効または期限切れのトークンです", 401, "Invalid Token")

@bp.route("/auth/logout", methods=["POST"])
@safe_route
def auth_logout():
    """ログアウト処理"""
    auth_header = request.headers.get('X-Service-Auth')
    
    if auth_header:
        session_manager.delete_session(auth_header)
    
    return jsonify({"message": "ログアウトしました"}), 200

@bp.route("/users", methods=["GET"])
@safe_route
def get_users():
    """管理者ユーザー一覧を取得"""
    from app.models.user import User  # 遅延インポート
    
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active,
        "last_login": u.last_login.isoformat() if u.last_login else None,
        "created_at": u.created_at.isoformat() if u.created_at else None
    } for u in users])

@bp.route("/users", methods=["POST"])
@safe_api_route(required_fields=["username", "email", "password"])
def create_user():
    """管理者ユーザーを作成"""
    from app.models.user import User  # 遅延インポート
    
    data = request.get_json()
    
    # 本来はパスワードハッシュ化を行う
    user = User(
        username=data["username"],
        email=data["email"],
        password_hash=data["password"],  # 実際の実装ではハッシュ化する
        role=data.get("role", "admin"),
        is_active=data.get("is_active", True)
    )
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "message": "ユーザーが正常に作成されました"
    }), 201

@bp.route("/users/<int:user_id>", methods=["PUT"])
@safe_route
def update_user(user_id):
    """管理者ユーザーを更新"""
    from app.models.user import User  # 遅延インポート
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if not data:
        return create_error_response("JSONデータが必要です", 400, "Missing JSON Data")
        return jsonify({"error": "No data provided"}), 400
    
    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    if "role" in data:
        user.role = data["role"]
    if "is_active" in data:
        user.is_active = data["is_active"]
    if "last_login" in data:
        user.last_login = now_jst()
    
    user.updated_at = now_jst()
    db.session.commit()
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "message": "ユーザーが正常に更新されました"
    })

@bp.route("/auth/set-session", methods=["POST"])
@safe_api_route(required_fields=["token"])
def set_session():
    """外部からのトークンを使用してローカルセッションを設定"""
    data = request.get_json()
    token = data["token"]
    
    # トークンの有効性を確認
    session_data = session_manager.validate_session(token)
    
    if session_data:
        from app.models.user import User  # 遅延インポート
        user = User.query.get(session_data['user_id'])
        
        if user and user.is_active:
            # Flask sessionにユーザー情報を保存
            from flask import session
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            # Cookieにも設定
            response = jsonify({
                "status": "session_set",
                "user_id": user.id,
                "username": user.username
            })
            response.set_cookie('admin_session_token', token, httponly=True, secure=True)
            return response, 200
    
    return create_error_response("無効なトークンです", 401, "Invalid Token")
