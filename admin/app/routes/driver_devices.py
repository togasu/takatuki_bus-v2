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
        
        devices = api_client.get_driver_devices(driver_id=driver_id, is_active=is_active_bool)
        
        if devices is None:
            return jsonify({
                "success": False,
                "error": "Failed to fetch devices from driver service"
            }), 500
        
        return jsonify({
            "success": True,
            "total_devices": len(devices),
            "devices": devices
        })
        
    except Exception as e:
        logger.error(f"Error getting all devices: {e}")
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
