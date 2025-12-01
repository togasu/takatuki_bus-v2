from flask import Blueprint, request, jsonify
from app.database import db
from app.models import Driver
from app.models.driver_device import DriverDevice
from datetime import datetime
from app.utils.now_jst import now_jst
from app.utils.auth_utils import SessionManager
from app.utils.decorators import safe_api_route, safe_route
from app.utils.error_handlers import create_error_response
import secrets

bp = Blueprint("api", __name__, url_prefix="/api")

# セッションマネージャーのインスタンス
session_manager = SessionManager()

@bp.route("/auth/login", methods=["POST"])
@safe_api_route(required_fields=["username", "password"])
def auth_login():
    """ドライバー認証処理"""
    data = request.get_json()
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
            "driver_id": session_data['driver_id'],
            "driver_data": session_data['driver_data']
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

@bp.route("/drivers", methods=["GET"])
@safe_route
def get_drivers():
    """ドライバー一覧を取得（管理者サービス用）"""
    # クエリパラメータからフィルタ条件を取得
    is_active = request.args.get('is_active')
    search_query = request.args.get('search', '')
    
    query = Driver.query
    
    # アクティブ状態でフィルタ
    if is_active is not None:
        is_active_bool = is_active.lower() == 'true'
        query = query.filter_by(is_active=is_active_bool)
    
    # 検索クエリでフィルタ
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Driver.username.like(search_pattern),
                Driver.number.cast(db.String).like(search_pattern)
            )
        )
    
    drivers = query.order_by(Driver.created_at.desc()).all()
    
    return jsonify([{
        "id": d.id,
        "username": d.username,
        "number": d.number,
        "is_active": d.is_active,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None
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

@bp.route("/drivers/<int:driver_id>/toggle-status", methods=["POST"])
@safe_route
def toggle_driver_status(driver_id):
    """ドライバーのアクティブ状態を切り替え"""
    driver = Driver.query.get_or_404(driver_id)
    
    try:
        driver.is_active = not driver.is_active
        driver.updated_at = now_jst()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "id": driver.id,
            "username": driver.username,
            "is_active": driver.is_active,
            "message": f"ドライバー {driver.username} のステータスを{'有効' if driver.is_active else '無効'}に変更しました"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route("/drivers/<int:driver_id>", methods=["DELETE"])
@safe_route
def delete_driver(driver_id):
    """ドライバーを削除"""
    driver = Driver.query.get_or_404(driver_id)
    username = driver.username
    
    try:
        db.session.delete(driver)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"ドライバー {username} を削除しました"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===================================
# Driver Device Management APIs
# ===================================

@bp.route("/driver-devices", methods=["GET"])
@safe_route
def get_driver_devices():
    """ドライバーデバイス一覧を取得"""
    driver_id = request.args.get('driver_id', type=int)
    is_active = request.args.get('is_active')
    
    query = DriverDevice.query
    
    if driver_id:
        query = query.filter_by(driver_id=driver_id)
    
    if is_active is not None:
        is_active_bool = is_active.lower() == 'true'
        query = query.filter_by(is_active=is_active_bool)
    
    devices = query.order_by(DriverDevice.created_at.desc()).all()
    
    return jsonify([{
        "id": d.id,
        "driver_id": d.driver_id,
        "driver_username": d.driver.username if d.driver else None,
        "mac_address": d.mac_address,
        "device_name": d.device_name,
        "is_active": d.is_active,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        "last_used_at": d.last_used_at.isoformat() if d.last_used_at else None
    } for d in devices]), 200

@bp.route("/driver-devices/<int:device_id>", methods=["GET"])
@safe_route
def get_driver_device(device_id):
    """特定のドライバーデバイスを取得"""
    device = DriverDevice.query.get_or_404(device_id)
    
    return jsonify({
        "id": device.id,
        "driver_id": device.driver_id,
        "driver_username": device.driver.username if device.driver else None,
        "mac_address": device.mac_address,
        "device_name": device.device_name,
        "is_active": device.is_active,
        "created_at": device.created_at.isoformat() if device.created_at else None,
        "updated_at": device.updated_at.isoformat() if device.updated_at else None,
        "last_used_at": device.last_used_at.isoformat() if device.last_used_at else None
    }), 200

@bp.route("/driver-devices", methods=["POST"])
@safe_route
def create_driver_device():
    """ドライバーデバイスを作成"""
    data = request.get_json()
    
    if not data or 'driver_id' not in data or 'mac_address' not in data:
        return jsonify({
            "success": False,
            "error": "driver_id and mac_address are required"
        }), 400
    
    try:
        device = DriverDevice.add_device(
            driver_id=data['driver_id'],
            mac_address=data['mac_address'],
            device_name=data.get('device_name')
        )
        db.session.commit()
        
        return jsonify({
            "success": True,
            "id": device.id,
            "driver_id": device.driver_id,
            "mac_address": device.mac_address,
            "device_name": device.device_name,
            "message": "デバイスを登録しました"
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route("/driver-devices/<int:device_id>", methods=["PUT"])
@safe_route
def update_driver_device(device_id):
    """ドライバーデバイス情報を更新"""
    device = DriverDevice.query.get_or_404(device_id)
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "No data provided"
        }), 400
    
    try:
        if 'device_name' in data:
            device.device_name = data['device_name']
        if 'is_active' in data:
            device.is_active = data['is_active']
        
        device.updated_at = now_jst()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "id": device.id,
            "message": "デバイス情報を更新しました"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route("/driver-devices/<int:device_id>/toggle-status", methods=["POST"])
@safe_route
def toggle_driver_device_status(device_id):
    """ドライバーデバイスのアクティブ状態を切り替え"""
    device = DriverDevice.query.get_or_404(device_id)
    
    try:
        device.is_active = not device.is_active
        device.updated_at = now_jst()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "id": device.id,
            "is_active": device.is_active,
            "message": f"デバイス {device.device_name or device.mac_address} を{'有効' if device.is_active else '無効'}にしました"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route("/driver-devices/<int:device_id>", methods=["DELETE"])
@safe_route
def delete_driver_device(device_id):
    """ドライバーデバイスを削除"""
    device = DriverDevice.query.get_or_404(device_id)
    device_info = f"{device.device_name or device.mac_address}"
    
    try:
        db.session.delete(device)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"デバイス {device_info} を削除しました"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

