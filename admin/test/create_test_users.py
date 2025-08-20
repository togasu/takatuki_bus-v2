#!/usr/bin/env python3
"""
テスト用ユーザーを作成するスクリプト
"""

from app import create_app
from app.database import db

def create_test_users():
    """テスト用ユーザーを作成"""
    app = create_app()
    
    with app.app_context():
        # アプリケーションコンテキスト内でUserモデルをインポート
        from app.models.user import User
        
        # テストユーザーのデータ
        test_users = [
            {
                "username": "admin_test",
                "email": "admin@test.com",
                "password": "admin123",
                "role": "admin",
                "is_active": True
            },
            {
                "username": "normal_test",
                "email": "normal@test.com", 
                "password": "normal123",
                "role": "normal",
                "is_active": True
            },
            {
                "username": "guest_test",
                "email": "guest@test.com",
                "password": "guest123", 
                "role": "guest",
                "is_active": True
            }
        ]
        
        for user_data in test_users:
            # 既存のユーザーがいるかチェック
            existing_user = User.query.filter_by(username=user_data["username"]).first()
            
            if existing_user:
                print(f"ユーザー '{user_data['username']}' は既に存在します。")
                continue
            
            # 新しいユーザーを作成
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"],
                is_active=user_data["is_active"]
            )
            
            # パスワードをハッシュ化して設定
            user.set_password(user_data["password"])
            
            db.session.add(user)
            print(f"テストユーザー '{user_data['username']}' を作成しました。")
        
        try:
            db.session.commit()
            print("すべてのテストユーザーの作成が完了しました。")
        except Exception as e:
            db.session.rollback()
            print(f"エラーが発生しました: {e}")

def list_users():
    """現在のユーザー一覧を表示"""
    app = create_app()
    
    with app.app_context():
        # アプリケーションコンテキスト内でUserモデルをインポート
        from app.models.user import User
        
        users = User.query.all()
        print("\n現在のユーザー一覧:")
        print("-" * 60)
        print(f"{'ID':<5} {'ユーザー名':<15} {'メール':<25} {'ロール':<10} {'有効':<5}")
        print("-" * 60)
        
        for user in users:
            print(f"{user.id:<5} {user.username:<15} {user.email:<25} {user.role:<10} {'○' if user.is_active else '×':<5}")

def delete_test_users():
    """テストユーザーを削除"""
    app = create_app()
    
    with app.app_context():
        # アプリケーションコンテキスト内でUserモデルをインポート
        from app.models.user import User
        
        test_usernames = ["admin_test", "normal_test", "guest_test"]
        
        for username in test_usernames:
            user = User.query.filter_by(username=username).first()
            if user:
                db.session.delete(user)
                print(f"テストユーザー '{username}' を削除しました。")
            else:
                print(f"テストユーザー '{username}' は見つかりませんでした。")
        
        try:
            db.session.commit()
            print("テストユーザーの削除が完了しました。")
        except Exception as e:
            db.session.rollback()
            print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "create":
            create_test_users()
        elif sys.argv[1] == "list":
            list_users()
        elif sys.argv[1] == "delete":
            delete_test_users()
        else:
            print("使用方法: python create_test_users.py [create|list|delete]")
    else:
        print("テストユーザーを作成します...")
        create_test_users()
        print("\n作成後のユーザー一覧:")
        list_users()
