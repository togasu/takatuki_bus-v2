#!/usr/bin/env python3
"""
権限システムのテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.user import User
from app.models.permission import Permission
from init_permissions import init_permissions

def test_permission_system():
    """権限システムのテスト"""
    app = create_app()
    
    with app.app_context():
        # データベースを初期化
        db.create_all()
        
        # 権限を初期化
        init_permissions()
        
        # テストユーザーを作成
        test_users = [
            {
                "username": "guest_user",
                "email": "guest@example.com",
                "password_hash": "hashed_password",
                "role": "guest"
            },
            {
                "username": "normal_user",
                "email": "normal@example.com",
                "password_hash": "hashed_password",
                "role": "normal"
            },
            {
                "username": "admin_user",
                "email": "admin@example.com",
                "password_hash": "hashed_password",
                "role": "admin"
            }
        ]
        
        # 既存のテストユーザーを削除
        for test_user_data in test_users:
            existing_user = User.query.filter_by(username=test_user_data["username"]).first()
            if existing_user:
                db.session.delete(existing_user)
        
        # テストユーザーを作成
        created_users = []
        for test_user_data in test_users:
            user = User(
                username=test_user_data["username"],
                email=test_user_data["email"],
                password_hash=test_user_data["password_hash"],
                role=test_user_data["role"]
            )
            db.session.add(user)
            created_users.append(user)
        
        db.session.commit()
        
        print("=== 権限システムテスト ===")
        
        # 各ユーザーの権限をテスト
        for user in created_users:
            print(f"\n{user.username} ({user.role}) の権限:")
            permissions = user.get_permissions()
            for perm in permissions:
                print(f"  - {perm}")
            
            print(f"\n{user.username} の権限チェック:")
            test_cases = [
                ("student_bus", "read"),
                ("student_seat", "read"),
                ("admin_user", "create"),
                ("admin_user", "delete"),
                ("admin_user", "read"),
                ("admin_user", "update"),
                ("driver", "all"),
                ("student", "all")
            ]
            
            for resource, action in test_cases:
                has_perm = user.has_permission(resource, action)
                print(f"  {resource}:{action} -> {'✓' if has_perm else '✗'}")
        
        print("\n=== 権限システムテスト完了 ===")

if __name__ == "__main__":
    test_permission_system()
