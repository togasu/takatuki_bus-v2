from flask import Blueprint, request, jsonify, render_template
from app.authorization import require_permission
from app.api_client import AdminAPIClient
import logging

logger = logging.getLogger(__name__)

driver_device_bp = Blueprint("driver_device_api", __name__, url_prefix="/api/driver-devices")
driver_device_ui_bp = Blueprint("driver_device_ui", __name__, url_prefix="/driver-devices")

api_client = AdminAPIClient()

@driver_device_bp.route("", methods=["GET"])
@require_permission("driver_device", "read")
def get_all_driver_devices():
    """すべてのドライバーデバイスを取得（Driverサービス経由）"""
    try:
        driver_id = request.args.get('driver_id', type=int)
        is_active = request.args.get('is_active')
        
        is_active_bool = None
        if is_active == 'true':
            is_active_bool = True
        elif is_active == 'false':
            is_active_bool = False
        
        # デバイス一覧を取得
        devices_response = api_client.get_driver_devices(driver_id=driver_id, is_active=is_active_bool)
        
        logger.info(f"Driver service response type: {type(devices_response)}")
        
        if devices_response is None:
            return jsonify({
                "success": False,
                "error": "Failed to fetch devices from driver service"
            }), 500
        
        # レスポンスがリストかどうか確認
        if isinstance(devices_response, list):
            devices = devices_response
        elif isinstance(devices_response, dict):
            # 辞書形式の場合、devicesキーから取得を試みる
            devices = devices_response.get('devices', [])
        else:
            logger.error(f"Unexpected response format: {type(devices_response)}")
            devices = []
        
        # 全ドライバー情報を取得
        drivers_response = api_client.get_drivers()
        drivers_map = {}
        
        logger.info(f"Drivers response type: {type(drivers_response)}")
        logger.info(f"Drivers response: {drivers_response}")
        
        if drivers_response:
            # ドライバーをマップに変換（usernameをキーに）
            for driver in drivers_response:
                username = driver.get('username')
                if username:
                    drivers_map[username] = {
                        'id': driver.get('id'),
                        'username': username,
                        'number': driver.get('number'),
                        'is_active': driver.get('is_active', True)
                    }
        
        logger.info(f"Drivers map: {drivers_map}")
        
        # デバイスをドライバーごとにグループ化
        devices_by_user = {}
        driver_info = {}  # ドライバー情報を保持
        
        # まず全ドライバーをdriver_infoに追加
        for username, info in drivers_map.items():
            driver_info[username] = info
        
        for device in devices:
            # driver_usernameまたはdriver_idでグループ化
            driver_username = device.get('driver_username')
            driver_key = driver_username or device.get('driver_name') or f"Driver {device.get('driver_id', 'Unknown')}"
            
            if driver_key not in devices_by_user:
                devices_by_user[driver_key] = []
                # ドライバー情報を保存（まだ存在しない場合のみ）
                if driver_key not in driver_info:
                    if driver_username and driver_username in drivers_map:
                        driver_info[driver_key] = drivers_map[driver_username]
                    else:
                        driver_info[driver_key] = {
                            'id': device.get('driver_id'),
                            'username': driver_key
                        }
            
            devices_by_user[driver_key].append(device)
        
        # デバイスを持たないドライバーも追加
        for username, info in drivers_map.items():
            if username not in devices_by_user:
                devices_by_user[username] = []
        
        logger.info(f"Driver info built: {driver_info}")
        logger.info(f"Devices by user: {list(devices_by_user.keys())}")
        
        return jsonify({
            "success": True,
            "total_devices": len(devices),
            "total_users": len(devices_by_user),
            "devices": devices,
            "devices_by_user": devices_by_user,
            "driver_info": driver_info,
            "all_drivers": list(drivers_map.values())  # 全ドライバーリスト
        })
        
    except Exception as e:
        logger.error(f"Error getting all devices: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

@driver_device_bp.route("/<int:device_id>", methods=["GET"])
@require_permission("driver_device", "read")
def get_driver_device(device_id):
    """特定のドライバーデバイスを取得（Driverサービス経由）"""
    try:
        device = api_client.get_driver_device_by_id(device_id)
        
        if device is None:
            return jsonify({
                "success": False,
                "error": "Device not found"
            }), 404
        
        return jsonify({
            "success": True,
            "device": device
        })
        
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@driver_device_bp.route("", methods=["POST"])
@require_permission("driver_device", "create")
def add_driver_device():
    """ドライバーに新しいデバイスを追加（Driverサービス経由）"""
    try:
        data = request.get_json()
        
        if not data or "driver_id" not in data or "mac_address" not in data:
            return jsonify({
                "success": False,
                "error": "driver_id and mac_address are required"
            }), 400
        
        result = api_client.create_driver_device(data)
        
        if result and result.get('success'):
            logger.info(f"Device added for driver_id {data['driver_id']}: {data['mac_address']}")
            return jsonify(result), 201
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to create device') if result else 'Communication error'
            }), 400
        
    except Exception as e:
        logger.error(f"Error adding device: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@driver_device_bp.route("/<int:device_id>", methods=["PUT"])
@require_permission("driver_device", "update")
def update_driver_device(device_id):
    """ドライバーデバイス情報を更新（Driverサービス経由）"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided"
            }), 400
        
        result = api_client.update_driver_device(device_id, data)
        
        if result and result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to update device') if result else 'Communication error'
            }), 400
        
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@driver_device_bp.route("/<int:device_id>/toggle-status", methods=["POST"])
@require_permission("driver_device", "update")
def toggle_driver_device_status(device_id):
    """ドライバーデバイスのアクティブ状態を切り替え（Driverサービス経由）"""
    try:
        result = api_client.toggle_driver_device_status(device_id)
        
        if result and result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to toggle device status') if result else 'Communication error'
            }), 500
        
    except Exception as e:
        logger.error(f"Error toggling device status {device_id}: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@driver_device_bp.route("/<int:device_id>", methods=["DELETE"])
@require_permission("driver_device", "delete")
def remove_driver_device(device_id):
    """ドライバーのデバイスを削除（Driverサービス経由）"""
    try:
        result = api_client.delete_driver_device(device_id)
        
        if result and result.get('success'):
            logger.info(f"Device {device_id} removed")
            return jsonify(result), 200
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Failed to delete device') if result else 'Communication error'
            }), 500
        
    except Exception as e:
        logger.error(f"Error removing device {device_id}: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

# UI Routes
@driver_device_ui_bp.route("/", methods=["GET"])
@require_permission("driver_device", "read")
def device_management_ui():
    """デバイス管理UI"""
    return render_template("driver_devices.html")
