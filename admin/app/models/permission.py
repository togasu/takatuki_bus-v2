from app.database import db
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.authorization import require_permission
from app.utils.now_jst import now_jst

class Permission(db.Model):
    """権限テーブル"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    resource = db.Column(db.String(100), nullable=False)  # リソース名
    action = db.Column(db.String(50), nullable=False)  # アクション (read, write, delete)
    role = db.Column(db.String(20), nullable=False)  # ロール (admin, normal, guest)
    is_allowed = db.Column(db.Boolean, default=True, nullable=False)  # 許可するかどうか
    created_at = db.Column(db.DateTime, default=now_jst)
    updated_at = db.Column(db.DateTime, default=now_jst, onupdate=now_jst)
    
    def __repr__(self):
        return f'<Permission {self.resource}.{self.action} for {self.role}>'

# Blueprint for Permission API
permission_bp = Blueprint("permission_api", __name__, url_prefix="/api/permissions")

@permission_bp.route("", methods=["GET"])
@require_permission("permission", "read")
def get_permissions():
    """権限一覧を取得"""
    permissions = Permission.query.all()
    return jsonify([{
        "id": p.id,
        "resource": p.resource,
        "action": p.action,
        "role": p.role,
        "is_allowed": p.is_allowed,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None
    } for p in permissions])

@permission_bp.route("", methods=["POST"])
@require_permission("permission", "create")
def create_permission():
    """権限を作成"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ["resource", "action", "role"]):
        return jsonify({"error": "Missing required fields: resource, action, role"}), 400
    
    try:
        permission = Permission(
            resource=data["resource"],
            action=data["action"],
            role=data["role"],
            is_allowed=data.get("is_allowed", True)
        )
        db.session.add(permission)
        db.session.commit()
        
        return jsonify({
            "id": permission.id,
            "resource": permission.resource,
            "action": permission.action,
            "role": permission.role,
            "is_allowed": permission.is_allowed,
            "message": "Permission created successfully"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
