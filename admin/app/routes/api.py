from flask import Blueprint, request, jsonify
from app.database import db
from datetime import datetime
from app.utils.now_jst import now_jst
from app.utils.auth_utils import SessionManager
import secrets
import os

bp = Blueprint("api", __name__, url_prefix="/api")

# セッションマネージャーのインスタンス
session_manager = SessionManager()

@bp.route("/auth/login", methods=["POST"])
def auth_login():
    """管理者認証処理"""
    from app.models.user import User  # 遅延インポート
    
    data = request.get_json()
    
    if not data or not all(k in data for k in ["username", "password"]):
        return jsonify({"error": "Missing username or password"}), 400
    
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
    
    return jsonify({"error": "Invalid credentials"}), 401

@bp.route("/auth/check", methods=["GET"])
def auth_check():
    """認証状態確認"""
    auth_header = request.headers.get('X-Service-Auth')
    
    if not auth_header:
        return jsonify({"error": "No authentication token"}), 401
    
    # Redisセッションから認証状態を確認
    session_data = session_manager.validate_session(auth_header)
    
    if session_data:
        return jsonify({
            "status": "authenticated",
            "user_id": session_data['user_id'],
            "user_data": session_data['user_data']
        }), 200
    
    return jsonify({"error": "Invalid or expired token"}), 401

@bp.route("/auth/logout", methods=["POST"])
def auth_logout():
    """ログアウト処理"""
    auth_header = request.headers.get('X-Service-Auth')
    
    if auth_header:
        session_manager.delete_session(auth_header)
    
    return jsonify({"message": "Logged out successfully"}), 200

@bp.route("/users", methods=["GET"])
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
def create_user():
    """管理者ユーザーを作成"""
    from app.models.user import User  # 遅延インポート
    
    data = request.get_json()
    
    if not data or not all(k in data for k in ["username", "email", "password"]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
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
            "message": "User created successfully"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    """管理者ユーザーを更新"""
    from app.models.user import User  # 遅延インポート
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
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
            "message": "User updated successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
