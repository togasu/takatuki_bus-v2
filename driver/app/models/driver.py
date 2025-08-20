from app.database import db
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.auth import admin_required
from app.utils.now_jst import now_jst
from app.utils.auth_utils import PasswordManager

class Driver(db.Model):
    """ドライバーテーブル"""
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.String(20), unique=True, nullable=False)  # ドライバーID
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)  # 運転免許証番号
    license_expiry = db.Column(db.Date, nullable=False)  # 免許証有効期限
    hire_date = db.Column(db.Date, nullable=False)  # 雇用日
    password_hash = db.Column(db.String(255))  # パスワードハッシュ
    password_salt = db.Column(db.String(255))  # パスワードsalt
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_jst)
    updated_at = db.Column(db.DateTime, default=now_jst, onupdate=now_jst)
    
    def __repr__(self):
        return f'<Driver {self.driver_id}: {self.name}>'
    
    def set_password(self, password: str):
        """パスワードを設定（ハッシュ化とsalt生成）"""
        if password:
            salt, password_hash = PasswordManager.hash_password(password)
            self.password_salt = salt
            self.password_hash = password_hash
    
    def check_password(self, password: str) -> bool:
        """パスワード検証"""
        if not self.password_hash or not self.password_salt:
            # パスワードが設定されていない場合は、driver_idのみで認証（デモ用）
            return bool(password)
        return PasswordManager.verify_password(password, self.password_salt, self.password_hash)

# Blueprint for Driver API
driver_bp = Blueprint("driver_api", __name__, url_prefix="/api/drivers")

@driver_bp.route("", methods=["GET"])
@admin_required
def get_drivers():
    """ドライバー一覧を取得"""
    drivers = Driver.query.all()
    return jsonify([{
        "id": d.id,
        "driver_id": d.driver_id,
        "name": d.name,
        "email": d.email,
        "phone": d.phone,
        "license_number": d.license_number,
        "license_expiry": d.license_expiry.isoformat() if d.license_expiry else None,
        "hire_date": d.hire_date.isoformat() if d.hire_date else None,
        "is_active": d.is_active,
        "created_at": d.created_at.isoformat() if d.created_at else None
    } for d in drivers])

@driver_bp.route("", methods=["POST"])
@admin_required
def create_driver():
    """ドライバーを作成"""
    data = request.get_json()
    
    required_fields = ["driver_id", "name", "email", "phone", "license_number", "license_expiry", "hire_date"]
    if not data or not all(k in data for k in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        driver = Driver(
            driver_id=data["driver_id"],
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            license_number=data["license_number"],
            license_expiry=datetime.strptime(data["license_expiry"], "%Y-%m-%d").date(),
            hire_date=datetime.strptime(data["hire_date"], "%Y-%m-%d").date(),
            is_active=data.get("is_active", True)
        )
        db.session.add(driver)
        db.session.commit()
        
        return jsonify({
            "id": driver.id,
            "driver_id": driver.driver_id,
            "name": driver.name,
            "message": "Driver created successfully"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@driver_bp.route("/<int:driver_id>", methods=["PUT"])
@admin_required
def update_driver(driver_id):
    """ドライバー情報を更新"""
    driver = Driver.query.get_or_404(driver_id)
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        if "name" in data:
            driver.name = data["name"]
        if "email" in data:
            driver.email = data["email"]
        if "phone" in data:
            driver.phone = data["phone"]
        if "license_expiry" in data:
            driver.license_expiry = datetime.strptime(data["license_expiry"], "%Y-%m-%d").date()
        if "is_active" in data:
            driver.is_active = data["is_active"]
        
        driver.updated_at = now_jst()
        db.session.commit()
        
        return jsonify({
            "id": driver.id,
            "driver_id": driver.driver_id,
            "name": driver.name,
            "message": "Driver updated successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
