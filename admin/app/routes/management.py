from flask import Blueprint, request, jsonify
from app.api_client import admin_api

bp = Blueprint("management", __name__, url_prefix="/management")

@bp.route("/students", methods=["GET"])
def manage_students():
    """学生管理 - 他のサービスの学生一覧を取得"""
    students = admin_api.get_students()
    if students is not None:
        return jsonify(students)
    else:
        return jsonify({"error": "Failed to fetch students"}), 500

@bp.route("/students", methods=["POST"])
def create_student_via_admin():
    """学生管理 - 他のサービスに学生を作成"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result = admin_api.create_student(data)
    if result is not None:
        return jsonify(result), 201
    else:
        return jsonify({"error": "Failed to create student"}), 500

@bp.route("/buses", methods=["GET"])
def manage_buses():
    """バス管理 - 他のサービスのバス一覧を取得"""
    buses = admin_api.get_buses()
    if buses is not None:
        return jsonify(buses)
    else:
        return jsonify({"error": "Failed to fetch buses"}), 500

@bp.route("/drivers", methods=["GET"])
def manage_drivers():
    """ドライバー管理 - 他のサービスのドライバー一覧を取得"""
    drivers = admin_api.get_drivers()
    if drivers is not None:
        return jsonify(drivers)
    else:
        return jsonify({"error": "Failed to fetch drivers"}), 500

@bp.route("/drivers", methods=["POST"])
def create_driver_via_admin():
    """ドライバー管理 - 他のサービスにドライバーを作成"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result = admin_api.create_driver(data)
    if result is not None:
        return jsonify(result), 201
    else:
        return jsonify({"error": "Failed to create driver"}), 500

@bp.route("/system/status", methods=["GET"])
def get_system_status():
    """システム全体のステータスを取得"""
    status = {
        "admin": "running",
        "services": {}
    }
    
    # 各サービスの稼働状況を確認
    try:
        students = admin_api.get_students()
        status["services"]["student"] = "running" if students is not None else "error"
    except:
        status["services"]["student"] = "error"
    
    try:
        drivers = admin_api.get_drivers()
        status["services"]["driver"] = "running" if drivers is not None else "error"
    except:
        status["services"]["driver"] = "error"
    
    return jsonify(status)
