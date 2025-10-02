from flask import Blueprint, request, jsonify
from app.api_client import admin_api
from app.authorization import require_permission

bp = Blueprint("management", __name__, url_prefix="/management")

@bp.before_request
def log_request():
    """リクエストの詳細をログに記録"""
    print(f"Management Blueprint - Method: {request.method}, Path: {request.path}")
    print(f"Endpoint: {request.endpoint}")
    print(f"Headers: {dict(request.headers)}")

@bp.errorhandler(405)
def method_not_allowed(error):
    """405 Method Not Allowedエラーハンドラー"""
    print(f"405 Error - Method: {request.method}, Path: {request.path}")
    print(f"Available methods for this endpoint: {error.description if hasattr(error, 'description') else 'Unknown'}")
    return jsonify({
        "error": True,
        "error_type": "Method Not Allowed",
        "message": "このメソッドは許可されていません",
        "status_code": 405,
        "request_method": request.method,
        "request_path": request.path
    }), 405

@bp.route("/test/no-auth", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
def test_no_auth():
    """認証なしのテストエンドポイント"""
    return jsonify({
        "message": "認証なしでアクセス成功",
        "method": request.method,
        "path": request.path,
        "timestamp": "2025-01-14"
    })

@bp.route("/test/students", methods=["GET", "POST", "OPTIONS"])
def test_students_no_auth():
    """認証なしの学生管理テストエンドポイント"""
    if request.method == "OPTIONS":
        return jsonify({"methods": ["GET", "POST", "OPTIONS"]}), 200
    
    if request.method == "GET":
        return jsonify({
            "message": "学生一覧取得テスト（認証なし）",
            "method": request.method,
            "students": ["test_student_1", "test_student_2"]
        })
    
    if request.method == "POST":
        data = request.get_json() or {}
        return jsonify({
            "message": "学生作成テスト（認証なし）",
            "method": request.method,
            "received_data": data
        }), 201

@bp.route("/students", methods=["GET"])
@require_permission("student", "read")
def manage_students():
    """学生管理 - 他のサービスの学生一覧を取得"""
    students = admin_api.get_students()
    if students is not None:
        return jsonify(students)
    else:
        return jsonify({"error": "Failed to fetch students"}), 500

@bp.route("/students", methods=["POST"])
@require_permission("student", "create")
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

@bp.route("/students/<student_id>", methods=["GET"])
@require_permission("student", "read")
def get_student_by_id(student_id):
    """学生管理 - 特定の学生情報を取得"""
    student = admin_api.get_student_by_id(student_id)
    if student is not None:
        return jsonify(student)
    else:
        return jsonify({"error": "Student not found"}), 404

@bp.route("/students/<student_id>", methods=["PUT"])
@require_permission("student", "update")
def update_student_via_admin(student_id):
    """学生管理 - 学生情報を更新"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result = admin_api.update_student(student_id, data)
    if result is not None:
        return jsonify(result)
    else:
        return jsonify({"error": "Failed to update student"}), 500

@bp.route("/students/<student_id>", methods=["DELETE"])
@require_permission("student", "delete")
def delete_student_via_admin(student_id):
    """学生管理 - 学生を削除"""
    result = admin_api.delete_student(student_id)
    if result is not None:
        return jsonify({"message": "Student deleted successfully"})
    else:
        return jsonify({"error": "Failed to delete student"}), 500

@bp.route("/buses", methods=["GET"])
@require_permission("bus", "read")
def manage_buses():
    """バス管理 - 他のサービスのバス一覧を取得"""
    buses = admin_api.get_buses()
    if buses is not None:
        return jsonify(buses)
    else:
        return jsonify({"error": "Failed to fetch buses"}), 500

@bp.route("/drivers", methods=["GET"])
@require_permission("driver", "read")
def manage_drivers():
    """ドライバー管理 - 他のサービスのドライバー一覧を取得"""
    drivers = admin_api.get_drivers()
    if drivers is not None:
        return jsonify(drivers)
    else:
        return jsonify({"error": "Failed to fetch drivers"}), 500

@bp.route("/drivers", methods=["POST"])
@require_permission("driver", "create")
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

@bp.route("/drivers/<driver_id>", methods=["GET"])
@require_permission("driver", "read")
def get_driver_by_id(driver_id):
    """ドライバー管理 - 特定のドライバー情報を取得"""
    driver = admin_api.get_driver_by_id(driver_id)
    if driver is not None:
        return jsonify(driver)
    else:
        return jsonify({"error": "Driver not found"}), 404

@bp.route("/drivers/<driver_id>", methods=["PUT"])
@require_permission("driver", "update")
def update_driver_via_admin(driver_id):
    """ドライバー管理 - ドライバー情報を更新"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result = admin_api.update_driver(driver_id, data)
    if result is not None:
        return jsonify(result)
    else:
        return jsonify({"error": "Failed to update driver"}), 500

@bp.route("/drivers/<driver_id>", methods=["DELETE"])
@require_permission("driver", "delete")
def delete_driver_via_admin(driver_id):
    """ドライバー管理 - ドライバーを削除"""
    result = admin_api.delete_driver(driver_id)
    if result is not None:
        return jsonify({"message": "Driver deleted successfully"})
    else:
        return jsonify({"error": "Failed to delete driver"}), 500

@bp.route("/system/status", methods=["GET"])
@require_permission("system", "read")
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

@bp.route("/students", methods=["OPTIONS"])
def students_options():
    """学生管理エンドポイントのOPTIONSハンドラー"""
    return jsonify({"methods": ["GET", "POST", "OPTIONS"]}), 200

@bp.route("/students/<student_id>", methods=["OPTIONS"])
def student_by_id_options(student_id):
    """個別学生管理エンドポイントのOPTIONSハンドラー"""
    return jsonify({"methods": ["GET", "PUT", "DELETE", "OPTIONS"]}), 200

@bp.route("/buses", methods=["OPTIONS"])
def buses_options():
    """バス管理エンドポイントのOPTIONSハンドラー"""
    return jsonify({"methods": ["GET", "OPTIONS"]}), 200

@bp.route("/drivers", methods=["OPTIONS"])
def drivers_options():
    """ドライバー管理エンドポイントのOPTIONSハンドラー"""
    return jsonify({"methods": ["GET", "POST", "OPTIONS"]}), 200

@bp.route("/drivers/<driver_id>", methods=["OPTIONS"])
def driver_by_id_options(driver_id):
    """個別ドライバー管理エンドポイントのOPTIONSハンドラー"""
    return jsonify({"methods": ["GET", "PUT", "DELETE", "OPTIONS"]}), 200

@bp.route("/system/status", methods=["OPTIONS"])
def system_status_options():
    """システムステータスエンドポイントのOPTIONSハンドラー"""
    return jsonify({"methods": ["GET", "OPTIONS"]}), 200

@bp.route("/debug/routes", methods=["GET"])
def debug_management_routes():
    """デバッグ用：管理ルートを表示"""
    from flask import current_app
    management_routes = []
    for rule in current_app.url_map.iter_rules():
        if rule.rule.startswith("/management"):
            management_routes.append({
                "endpoint": rule.endpoint,
                "rule": rule.rule,
                "methods": list(rule.methods)
            })
    return jsonify({
        "management_routes": management_routes,
        "total_management_routes": len(management_routes)
    })

@bp.route("/", methods=["GET"])
def management_api_info():
    """管理APIの情報を提供"""
    return jsonify({
        "service": "Management API",
        "version": "1.0",
        "endpoints": {
            "/students": {
                "methods": ["GET", "POST", "OPTIONS"],
                "description": "学生管理"
            },
            "/students/<id>": {
                "methods": ["GET", "PUT", "DELETE", "OPTIONS"],
                "description": "個別学生管理"
            },
            "/buses": {
                "methods": ["GET", "OPTIONS"],
                "description": "バス管理"
            },
            "/drivers": {
                "methods": ["GET", "POST", "OPTIONS"],
                "description": "ドライバー管理"
            },
            "/drivers/<id>": {
                "methods": ["GET", "PUT", "DELETE", "OPTIONS"],
                "description": "個別ドライバー管理"
            },
            "/system/status": {
                "methods": ["GET", "OPTIONS"],
                "description": "システムステータス"
            }
        }
    })

@bp.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def catch_all(path):
    """存在しないエンドポイントをキャッチ"""
    return jsonify({
        "error": True,
        "error_type": "Not Found",
        "message": f"エンドポイント '/{path}' は存在しません",
        "status_code": 404,
        "available_endpoints": [
            "/management/",
            "/management/students",
            "/management/students/<id>",
            "/management/buses",
            "/management/drivers",
            "/management/drivers/<id>",
            "/management/system/status"
        ]
    }), 404
