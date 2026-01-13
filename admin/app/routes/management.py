from flask import Blueprint, request, jsonify, render_template
from app.api_client import admin_api
from app.authorization import require_permission
from datetime import datetime, timedelta

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

@bp.route("/buses/ui", methods=["GET"])
@require_permission("bus", "read")
def bus_management_ui():
    """バス管理UI"""
    return render_template('bus_management.html')

@bp.route("/buses/recurring", methods=["POST"])
@require_permission("bus", "create")
def create_recurring_bus():
    """指定曜日の定期バス作成"""
    try:
        data = request.get_json()
        day_of_week = data.get('dayOfWeek')  # 0=日曜日, 1=月曜日, ..., 6=土曜日
        time = data.get('time')  # HH:MM形式
        direction = data.get('direction')  # 0=上り, 1=下り
        seats = data.get('seats', 45)
        count = data.get('count', 48)  # デフォルトは48回（約12ヶ月分）
        
        # 曜日のバリデーション
        if day_of_week is None or not isinstance(day_of_week, int) or day_of_week < 0 or day_of_week > 6:
            return jsonify({"error": "曜日は0〜6の整数で指定してください（0=日曜日, 6=土曜日）"}), 400
        
        if not time:
            return jsonify({"error": "時刻は必須です"}), 400
        
        # 時刻の形式チェック
        try:
            time_parts = time.split(':')
            if len(time_parts) != 2:
                raise ValueError("時刻はHH:MM形式で指定してください")
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError("有効な時刻を指定してください")
        except ValueError as e:
            return jsonify({"error": f"時刻の形式が不正です: {str(e)}"}), 400
        
        # 指定曜日の日付を取得
        target_dates = get_future_weekdays(day_of_week, count)
        
        created_buses = []
        failed_buses = []
        
        for date in target_dates:
            # 時刻を組み合わせてdatetimeオブジェクトを作成
            departure_datetime = date.replace(
                hour=hour, 
                minute=minute, 
                second=0, 
                microsecond=0
            )
            
            # APIを通じてバスを作成
            bus_data = {
                'departure_time': departure_datetime.isoformat(),
                'seats': seats,
                'direction': direction
            }
            
            result = admin_api.create_bus(bus_data)
            if result:
                created_buses.append(result)
            else:
                failed_buses.append(departure_datetime.isoformat())
        
        weekday_names = ['日曜日', '月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日']
        
        response = {
            "message": f"毎週{weekday_names[day_of_week]} {time}のバスを{len(created_buses)}個作成しました",
            "created_count": len(created_buses),
            "failed_count": len(failed_buses),
            "buses": created_buses
        }
        
        if failed_buses:
            response["failed_buses"] = failed_buses
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": f"バス作成中にエラーが発生しました: {str(e)}"}), 500

def get_future_weekdays(day_of_week, count=52):
    """
    今後の指定曜日の日付を取得
    
    Args:
        day_of_week: 0=日曜日, 1=月曜日, ..., 6=土曜日
        count: 取得する日数
    
    Returns:
        指定曜日のdatetimeオブジェクトのリスト
    """
    dates = []
    today = datetime.now().date()
    
    # 次の指定曜日を見つける
    # Pythonのweekday()は0=月曜日、6=日曜日
    # 引数のday_of_weekは0=日曜日、6=土曜日なので変換が必要
    # day_of_week: 0(日) -> weekday: 6, 1(月) -> 0, 2(火) -> 1, ..., 6(土) -> 5
    target_weekday = (day_of_week + 6) % 7  # 0(日)->6, 1(月)->0, 2(火)->1, ..., 6(土)->5
    
    current_weekday = today.weekday()
    days_until_target = (target_weekday - current_weekday) % 7
    
    if days_until_target == 0:  # 今日が指定曜日の場合
        days_until_target = 7  # 来週の同じ曜日から開始
    
    next_target_day = today + timedelta(days=days_until_target)
    
    # 指定された数の日付を生成
    for i in range(count):
        target_date = next_target_day + timedelta(weeks=i)
        dates.append(datetime.combine(target_date, datetime.min.time()))
    
    return dates

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
