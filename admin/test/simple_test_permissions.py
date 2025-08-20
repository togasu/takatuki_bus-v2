#!/usr/bin/env python3
"""
権限システムのテスト用簡易アプリ
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 簡易テスト用のFlaskアプリ
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_permissions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DBインスタンスを作成
db = SQLAlchemy(app)

# カスタムのデータベースオブジェクトを作成して、既存のモデルで使用されるdbと同じインターフェースを提供
class MockDatabase:
    def __init__(self, db_instance):
        self.db_instance = db_instance
        self.Model = db_instance.Model
        self.Column = db_instance.Column
        self.Integer = db_instance.Integer
        self.String = db_instance.String
        self.Text = db_instance.Text
        self.Boolean = db_instance.Boolean
        self.DateTime = db_instance.DateTime
        self.session = db_instance.session

# app.databaseモジュールを模擬
sys.modules['app.database'] = type('MockModule', (), {'db': MockDatabase(db)})()

# モデルを定義
with app.app_context():
    from app.models.user import User
    from app.models.permission import Permission
    
    # テーブルを作成
    db.create_all()
    
    print("=== 権限システムの初期化 ===")
    
    # 権限を初期化
    Permission.query.delete()
    
    # 基本権限を定義
    permissions = [
        # Guest権限
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
        
        # Normal権限
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
        
        # Admin権限
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
    
    # テストユーザーを作成
    User.query.delete()
    
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
    print(f"{len(created_users)}人のテストユーザーを作成しました。")
    
    print("\n=== 権限システムテスト ===")
    
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
        ]
        
        for resource, action in test_cases:
            has_perm = user.has_permission(resource, action)
            print(f"  {resource}:{action} -> {'✓' if has_perm else '✗'}")
    
    print("\n=== 権限システムテスト完了 ===")
    
    # 権限一覧を表示
    print("\n=== 登録済み権限一覧 ===")
    all_permissions = Permission.query.all()
    for perm in all_permissions:
        print(f"- {perm.permission_name}: {perm.description} ({perm.resource}:{perm.action})")
