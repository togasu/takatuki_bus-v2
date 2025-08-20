from app.database import db
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.authorization import require_permission
from app.utils.now_jst import now_jst

class Permission(db.Model):
    """権限テーブル"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    permission_name = db.Column(db.String(50), unique=True, nullable=False)  # 権限名
    description = db.Column(db.Text)  # 権限の説明
    resource = db.Column(db.String(50), nullable=False)  # リソース名
    action = db.Column(db.String(20), nullable=False)  # アクション (read, write, delete)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_jst)
    
    def __repr__(self):
        return f'<Permission {self.permission_name}>'

# Blueprint for Permission API
permission_bp = Blueprint("permission_api", __name__, url_prefix="/api/permissions")

@permission_bp.route("", methods=["GET"])
@require_permission("admin_permission", "read")
def get_permissions():
    """権限一覧を取得"""
    permissions = Permission.query.all()
    return jsonify([{
        "id": p.id,
        "permission_name": p.permission_name,
        "description": p.description,
        "resource": p.resource,
        "action": p.action,
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat() if p.created_at else None
    } for p in permissions])

@permission_bp.route("", methods=["POST"])
@require_permission("admin_permission", "create")
def create_permission():
    """権限を作成"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ["permission_name", "resource", "action"]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        permission = Permission(
            permission_name=data["permission_name"],
            description=data.get("description"),
            resource=data["resource"],
            action=data["action"],
            is_active=data.get("is_active", True)
        )
        db.session.add(permission)
        db.session.commit()
        
        return jsonify({
            "id": permission.id,
            "permission_name": permission.permission_name,
            "resource": permission.resource,
            "action": permission.action,
            "message": "Permission created successfully"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
