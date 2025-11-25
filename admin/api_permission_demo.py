#!/usr/bin/env python3
"""
権限システムの使用例とAPIデコレータのサンプル
"""

from functools import wraps
from flask import Flask, jsonify, request

app = Flask(__name__)

# モック用のユーザーデータ
mock_users = {
    "guest_token": {"username": "guest_user", "role": "guest"},
    "normal_token": {"username": "normal_user", "role": "normal"},
    "admin_token": {"username": "admin_user", "role": "admin"}
}

def get_current_user():
    """リクエストヘッダーからユーザーを取得する模擬実装"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    return mock_users.get(token)

def has_permission(user, resource, action):
    """権限チェック関数"""
    if not user:
        return False
    
    user_role = user["role"]
    
    if user_role == "admin":
        return True
    elif user_role == "normal":
        # アカウント作成・削除は禁止
        if resource == "admin_user" and action in ["create", "delete"]:
            return False
        allowed_resources = [
            "admin_user", "admin_permission", "driver", "student",
            "student_bus", "student_seat", "student_course", "student_season"
        ]
        return resource in allowed_resources
    elif user_role == "guest":
        allowed_permissions = [
            ("student_bus", "read"),
            ("student_seat", "read")
        ]
        return (resource, action) in allowed_permissions
    
    return False

def require_permission(resource, action):
    """権限チェックデコレータ"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            
            if not has_permission(user, resource, action):
                return jsonify({
                    "error": "Insufficient permissions",
                    "required_permission": f"{resource}:{action}",
                    "user_role": user["role"]
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(allowed_roles):
    """ロールチェックデコレータ"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            
            if user["role"] not in allowed_roles:
                return jsonify({
                    "error": "Insufficient role",
                    "required_roles": allowed_roles,
                    "user_role": user["role"]
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# APIエンドポイントの例

@app.route("/api/bus", methods=["GET"])
@require_permission("student_bus", "read")
def get_bus_info():
    """バス情報を取得 - guest, normal, admin がアクセス可能"""
    return jsonify({
        "buses": [
            {"id": 1, "route": "Route A", "capacity": 50},
            {"id": 2, "route": "Route B", "capacity": 40}
        ]
    })

@app.route("/api/seats", methods=["GET"])
@require_permission("student_seat", "read")
def get_seat_info():
    """座席情報を取得 - guest, normal, admin がアクセス可能"""
    return jsonify({
        "seats": [
            {"id": 1, "bus_id": 1, "seat_number": "A1", "status": "available"},
            {"id": 2, "bus_id": 1, "seat_number": "A2", "status": "occupied"}
        ]
    })

@app.route("/api/users", methods=["GET"])
@require_permission("admin_user", "read")
def get_users():
    """ユーザー一覧を取得 - normal, admin がアクセス可能"""
    return jsonify({
        "users": [
            {"id": 1, "username": "user1", "role": "normal"},
            {"id": 2, "username": "user2", "role": "admin"}
        ]
    })

@app.route("/api/users", methods=["POST"])
@require_permission("admin_user", "create")
def create_user():
    """ユーザーを作成 - admin のみアクセス可能"""
    return jsonify({"message": "User created successfully"})

@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@require_permission("admin_user", "delete")
def delete_user(user_id):
    """ユーザーを削除 - admin のみアクセス可能"""
    return jsonify({"message": f"User {user_id} deleted successfully"})

@app.route("/api/driver", methods=["GET"])
@require_permission("driver", "read")
def get_drivers():
    """ドライバー情報を取得 - normal, admin がアクセス可能"""
    return jsonify({
        "drivers": [
            {"id": 1, "name": "Driver A", "license": "ABC123"},
            {"id": 2, "name": "Driver B", "license": "DEF456"}
        ]
    })

@app.route("/api/health", methods=["GET"])
@require_role(["guest", "normal", "admin"])
def health_check():
    """ヘルスチェック - すべてのロールがアクセス可能"""
    user = get_current_user()
    return jsonify({
        "status": "OK",
        "user": user["username"] if user else "anonymous",
        "role": user["role"] if user else "none"
    })

if __name__ == "__main__":
    print("=== 権限システム API サンプル ===")
    print()
    print("テスト用のトークン:")
    print("- Guest: guest_token")
    print("- Normal: normal_token") 
    print("- Admin: admin_token")
    print()
    print("使用例:")
    print("curl -H 'Authorization: Bearer guest_token' http://localhost:5000/api/bus")
    print("curl -H 'Authorization: Bearer normal_token' http://localhost:5000/api/users")
    print("curl -H 'Authorization: Bearer admin_token' http://localhost:5000/api/users -X POST")
    print()
    print("サーバーを起動します...")
    
    app.run(debug=True, port=5000)
