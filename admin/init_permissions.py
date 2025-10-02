#!/usr/bin/env python3
"""
権限システムの初期データを設定するスクリプト
"""

from app import create_app
from app.database import db
from app.models.permission import Permission
from app.models.user import User

def init_permissions():
    """権限の初期データを作成"""
    app = create_app()
    
    with app.app_context():
        # 既存の権限をクリア
        Permission.query.delete()
        
        # 基本権限を定義
        permissions = [
            # Guest権限: studentのbusとseat（予約者名を除く）の個人情報を含まない情報のAPIのみ
            {
                "permission_name": "guest_bus_read",
                "description": "バス情報の読み取り（個人情報除く）",
                "resource": "student_bus",
                "action": "read"
            },
            {
                "permission_name": "guest_seat_read",
                "description": "座席情報の読み取り（予約者名除く）",
                "resource": "student_seat",
                "action": "read"
            },
            
            # Normal権限: アカウント作成・削除以外のすべて
            {
                "permission_name": "normal_user_read",
                "description": "ユーザー情報の読み取り",
                "resource": "admin_user",
                "action": "read"
            },
            {
                "permission_name": "normal_user_update",
                "description": "ユーザー情報の更新",
                "resource": "admin_user",
                "action": "update"
            },
            {
                "permission_name": "normal_permission_all",
                "description": "権限管理の全操作",
                "resource": "admin_permission",
                "action": "all"
            },
            {
                "permission_name": "normal_driver_all",
                "description": "ドライバー管理の全操作",
                "resource": "driver",
                "action": "all"
            },
            {
                "permission_name": "normal_student_all",
                "description": "学生情報の全操作",
                "resource": "student",
                "action": "all"
            },
            {
                "permission_name": "normal_bus_all",
                "description": "バス情報の全操作",
                "resource": "student_bus",
                "action": "all"
            },
            {
                "permission_name": "normal_seat_all",
                "description": "座席情報の全操作",
                "resource": "student_seat",
                "action": "all"
            },
            {
                "permission_name": "normal_course_all",
                "description": "コース情報の全操作",
                "resource": "student_course",
                "action": "all"
            },
            {
                "permission_name": "normal_season_all",
                "description": "シーズン情報の全操作",
                "resource": "student_season",
                "action": "all"
            },
            
            # Admin権限: すべての操作が可能
            {
                "permission_name": "admin_user_create",
                "description": "ユーザーアカウントの作成",
                "resource": "admin_user",
                "action": "create"
            },
            {
                "permission_name": "admin_user_delete",
                "description": "ユーザーアカウントの削除",
                "resource": "admin_user",
                "action": "delete"
            },
            {
                "permission_name": "admin_user_all",
                "description": "ユーザー管理の全操作",
                "resource": "admin_user",
                "action": "all"
            },
            {
                "permission_name": "admin_permission_all",
                "description": "権限管理の全操作",
                "resource": "admin_permission",
                "action": "all"
            },
            {
                "permission_name": "admin_driver_all",
                "description": "ドライバー管理の全操作",
                "resource": "driver",
                "action": "all"
            },
            {
                "permission_name": "admin_student_all",
                "description": "学生情報の全操作",
                "resource": "student",
                "action": "all"
            },
            {
                "permission_name": "admin_bus_all",
                "description": "バス情報の全操作",
                "resource": "student_bus",
                "action": "all"
            },
            {
                "permission_name": "admin_seat_all",
                "description": "座席情報の全操作",
                "resource": "student_seat",
                "action": "all"
            },
            {
                "permission_name": "admin_course_all",
                "description": "コース情報の全操作",
                "resource": "student_course",
                "action": "all"
            },
            {
                "permission_name": "admin_season_all",
                "description": "シーズン情報の全操作",
                "resource": "student_season",
                "action": "all"
            },
            {
                "permission_name": "admin_system_all",
                "description": "システム設定の全操作",
                "resource": "system",
                "action": "all"
            }
        ]
        
        # 権限を作成
        for perm_data in permissions:
            permission = Permission(
                permission_name=perm_data["permission_name"],
                description=perm_data["description"],
                resource=perm_data["resource"],
                action=perm_data["action"]
            )
            db.session.add(permission)
        
        db.session.commit()
        print(f"{len(permissions)}個の権限を作成しました。")

def get_role_permissions(role):
    """ロールに応じた権限リストを返す"""
    role_permissions = {
        "guest": [
            "guest_bus_read",
            "guest_seat_read"
        ],
        "normal": [
            "normal_user_read",
            "normal_user_update",
            "normal_permission_all",
            "normal_driver_all",
            "normal_student_all",
            "normal_bus_all",
            "normal_seat_all",
            "normal_course_all",
            "normal_season_all"
        ],
        "admin": [
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
            "admin_system_all"
        ]
    }
    return role_permissions.get(role, [])

if __name__ == "__main__":
    init_permissions()
    print("権限システムの初期化が完了しました。")
