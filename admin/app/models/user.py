from app.database import db
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.authorization import require_permission, require_role
from app.utils.now_jst import now_jst
from app.utils.auth_utils import PasswordManager

class User(db.Model):
    """管理者ユーザーテーブル"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    password_salt = db.Column(db.String(255), nullable=False)  # saltフィールド追加
    role = db.Column(db.String(20), default='admin')  # guest, normal, admin
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    last_logout = db.Column(db.DateTime)  # ログアウト時刻追加
    created_at = db.Column(db.DateTime, default=now_jst)
    updated_at = db.Column(db.DateTime, default=now_jst, onupdate=now_jst)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password: str):
        """パスワードを設定（ハッシュ化とsalt生成）"""
        salt, password_hash = PasswordManager.hash_password(password)
        self.password_salt = salt
        self.password_hash = password_hash
    
    def check_password(self, password: str) -> bool:
        """パスワード検証"""
        return PasswordManager.verify_password(password, self.password_salt, self.password_hash)
    
    def has_permission(self, resource, action):
        """ユーザーが指定されたリソースとアクションに対する権限を持っているかチェック"""
        from app.authorization import has_permission
        return has_permission(self, resource, action)
    
    def get_permissions(self):
        """ユーザーの権限リストを取得"""
        from app.authorization import get_user_permissions
        return get_user_permissions(self)
    
    def is_guest(self):
        """guestロールかどうか"""
        return self.role == 'guest'
    
    def is_normal(self):
        """normalロールかどうか"""
        return self.role == 'normal'
    
    def is_admin(self):
        """adminロールかどうか"""
        return self.role == 'admin'

# Blueprint for User API
user_bp = Blueprint("user_api", __name__, url_prefix="/api/users")

@user_bp.route("", methods=["GET"])
@require_permission("admin_user", "read")
def get_users():
    """管理者ユーザー一覧を取得"""
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active,
        "last_login": u.last_login.isoformat() if u.last_login else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "last_logout": u.last_logout.isoformat() if u.last_logout else None,
    } for u in users])

@user_bp.route("", methods=["POST"])
@require_permission("admin_user", "create")
def create_user():
    """管理者ユーザーを作成"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ["username", "email", "password"]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        user = User(
            username=data["username"],
            email=data["email"],
            role=data.get("role", "admin"),
            is_active=data.get("is_active", True)
        )
        
        # パスワードをハッシュ化して設定
        user.set_password(data["password"])
        
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

@user_bp.route("/<int:user_id>", methods=["PUT"])
@require_permission("admin_user", "update")
def update_user(user_id):
    """管理者ユーザーを更新"""
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

@user_bp.route("/<int:user_id>", methods=["DELETE"])
@require_permission("admin_user", "delete")
def delete_user(user_id):
    """管理者ユーザーを削除"""
    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            "message": "User deleted successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@user_bp.route("/permissions", methods=["GET"])
@require_permission("admin_user", "read")
def get_user_permissions():
    """現在のユーザーの権限を取得"""
    from app.auth import get_current_user
    
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    permissions = user.get_permissions()
    
    return jsonify({
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "permissions": permissions
    })
