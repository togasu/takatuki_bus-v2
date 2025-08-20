from flask import Blueprint, request, jsonify
from app.database import db
from app.models import Driver
from datetime import datetime
from app.utils.now_jst import now_jst
from app.utils.auth_utils import SessionManager
import secrets

bp = Blueprint("api", __name__, url_prefix="/api")

# セッションマネージャーのインスタンス
session_manager = SessionManager()

@bp.route("/auth/login", methods=["POST"])
def auth_login():
    """ドライバー認証処理"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ["username", "password"]):
        return jsonify({"error": "Missing username or password"}), 400
    
    username = data["username"]
    password = data["password"]
    
    # ドライバー認証（実際のパスワード検証）
    driver = Driver.query.filter_by(driver_id=username, is_active=True).first()
    
    if driver and driver.check_password(password):
        # 認証成功時にRedisセッションを作成
        driver_data = {
            "driver_id": driver.driver_id,
            "name": driver.name,
            "email": driver.email
        }
        
        session_token = session_manager.create_session(driver.driver_id, driver_data)
        
        return jsonify({
            "token": session_token,
            "driver_id": driver.driver_id,
            "name": driver.name
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
            "driver_id": session_data['driver_id'],
            "driver_data": session_data['driver_data']
        }), 200
    
    return jsonify({"error": "Invalid or expired token"}), 401

@bp.route("/auth/logout", methods=["POST"])
def auth_logout():
    """ログアウト処理"""
    auth_header = request.headers.get('X-Service-Auth')
    
    if auth_header:
        session_manager.delete_session(auth_header)
    
    return jsonify({"message": "Logged out successfully"}), 200

@bp.route("/drivers", methods=["GET"])
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

@bp.route("/drivers", methods=["POST"])
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

@bp.route("/drivers/<int:driver_id>", methods=["PUT"])
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
