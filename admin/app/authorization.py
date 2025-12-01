"""
認可機能を提供するモジュール
"""

from functools import wraps
from flask import request, jsonify, redirect, url_for, g
from app.auth import get_current_user

def require_permission(resource, action):
    """
    権限チェックデコレータ
    
    Args:
        resource (str): リソース名
        action (str): アクション名
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            import logging
            
            logger = logging.getLogger(__name__)
            logger.info(f"=== Authorization check for {request.path} ===")
            logger.info(f"Required permission: {resource}:{action}")
            logger.info(f"Request method: {request.method}")
            logger.info(f"Request headers: {dict(request.headers)}")
            
            # 現在のユーザーを取得
            user = get_current_user()
            logger.info(f"Current user: {user.username if user else None}")
            
            if not user:
                # APIリクエストまたはAJAXリクエストの判定を改善
                is_api_request = (
                    'application/json' in request.headers.get('Content-Type', '') or
                    'application/json' in request.headers.get('Accept', '') or
                    request.path.startswith('/api/') or
                    request.path.startswith('/student_management/') or  # 学生管理APIも含める
                    request.headers.get('X-Requested-With') == 'XMLHttpRequest'  # AJAX判定
                )
                
                logger.info(f"Is API request: {is_api_request}")
                logger.warning("No user found - authentication required")
                
                if is_api_request:
                    logger.info("Returning JSON error for API request")
                    return jsonify({"error": "Authentication required"}), 401
                # HTMLページのリクエストの場合はログインページにリダイレクト
                logger.info("Redirecting to login page for web request")
                return redirect(url_for('index.login'))
            
            # 権限チェック
            has_perm = has_permission(user, resource, action)
            logger.info(f"User role: {user.role}")
            logger.info(f"Permission check result: {has_perm}")
            
            if not has_perm:
                # APIリクエストまたはAJAXリクエストの判定を改善
                is_api_request = (
                    'application/json' in request.headers.get('Content-Type', '') or
                    'application/json' in request.headers.get('Accept', '') or
                    request.path.startswith('/api/') or
                    request.path.startswith('/student_management/') or  # 学生管理APIも含める
                    request.headers.get('X-Requested-With') == 'XMLHttpRequest'  # AJAX判定
                )
                
                logger.warning(f"Permission denied for user {user.username}")
                
                if is_api_request:
                    return jsonify({"error": "Insufficient permissions"}), 403
                # HTMLページのリクエストの場合はログインページにリダイレクト
                return redirect(url_for('index.login'))
            
            logger.info("Authorization successful")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def has_permission(user, resource, action):
    """
    ユーザーが指定されたリソースとアクションに対する権限を持っているかチェック
    
    Args:
        user (User): ユーザーオブジェクト
        resource (str): リソース名
        action (str): アクション名
    
    Returns:
        bool: 権限がある場合True
    """
    # ユーザーのロールを取得
    user_role = user.role
    
    # ロール別の権限チェック
    if user_role == "admin":
        # adminは全ての権限を持つ
        return True
    elif user_role == "normal":
        # normalは特定の権限を持つ
        return check_normal_permissions(resource, action)
    elif user_role == "guest":
        # guestは限定された権限のみ
        return check_guest_permissions(resource, action)
    
    return False

def check_guest_permissions(resource, action):
    """
    guest権限のチェック
    studentのbusとseat（予約者名を除く）の個人情報を含まない情報のAPIのみ
    """
    allowed_permissions = [
        ("student_bus", "read"),
        ("student_seat", "read")
    ]
    
    return (resource, action) in allowed_permissions

def check_normal_permissions(resource, action):
    """
    normal権限のチェック
    アカウント作成・削除以外のすべて
    """
    # アカウント作成・削除は禁止
    if resource == "admin_user" and action in ["create", "delete"]:
        return False
    
    # その他の操作は許可
    allowed_resources = [
        "admin_user",      # 読み取り・更新のみ
        "admin_permission",
        "admin",           # 学期管理等の管理者専用機能
        "driver",
        "student",
        "student_bus",
        "student_seat",
        "student_course",
        "student_season",
        "reservation"      # 予約確認機能
    ]
    
    return resource in allowed_resources

def get_user_permissions(user):
    """
    ユーザーの権限リストを取得
    
    Args:
        user (User): ユーザーオブジェクト
    
    Returns:
        list: 権限名のリスト
    """
    role = user.role
    
    if role == "guest":
        return [
            "guest_bus_read",
            "guest_seat_read"
        ]
    elif role == "normal":
        return [
            "normal_user_read",
            "normal_user_update",
            "normal_permission_all",
            "normal_driver_all",
            "normal_student_all",
            "normal_bus_all",
            "normal_seat_all",
            "normal_course_all",
            "normal_season_all"
        ]
    elif role == "admin":
        return [
            "admin_user_create",
            "admin_user_delete",
            "admin_user_all",
            "admin_permission_all",
            "admin_driver_all",
            "admin_student_all",
            "admin_bus_all",
            "admin_seat_all",
            "admin_course_all",
            "admin_season_all",
            "admin_system_all",
            "admin_semester_all",   # 学期管理権限を追加
            "admin_reservation_all"  # 予約確認権限を追加
        ]
    
    return []

def require_role(allowed_roles):
    """
    ロールチェックデコレータ
    
    Args:
        allowed_roles (list): 許可されたロールのリスト
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            
            if user.role not in allowed_roles:
                return jsonify({"error": "Insufficient role"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
