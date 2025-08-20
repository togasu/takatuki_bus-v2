#!/usr/bin/env python3
"""
テストユーザーでのログイン認証をテストするスクリプト（直接データベースアクセス）
"""

import psycopg2
import bcrypt
import os
import json
from datetime import datetime

def verify_password(password, salt, stored_hash):
    """パスワード検証"""
    try:
        salt_bytes = salt.encode('utf-8')
        # 入力されたパスワードをハッシュ化
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt_bytes)
        # ハッシュ比較
        return password_hash.decode('utf-8') == stored_hash
    except Exception as e:
        print(f"パスワード検証エラー: {e}")
        return False

def test_login(username, password):
    """ログインテスト"""
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'database': os.getenv('POSTGRES_DB', 'mydb'),
        'user': os.getenv('POSTGRES_USER', 'user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'pass'),
        'port': 5432
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # ユーザー情報を取得
        cur.execute(
            "SELECT id, username, email, password_hash, password_salt, role, is_active FROM users WHERE username = %s",
            (username,)
        )
        
        user_data = cur.fetchone()
        
        if not user_data:
            print(f"❌ ユーザー '{username}' が見つかりません")
            return False
        
        user_id, username, email, password_hash, password_salt, role, is_active = user_data
        
        if not is_active:
            print(f"❌ ユーザー '{username}' は無効化されています")
            return False
        
        # パスワード検証
        if verify_password(password, password_salt, password_hash):
            print(f"✅ ユーザー '{username}' のログイン成功！")
            print(f"   ID: {user_id}")
            print(f"   メール: {email}")
            print(f"   ロール: {role}")
            
            # ログイン時刻を更新
            cur.execute(
                "UPDATE users SET last_login = %s WHERE id = %s",
                (datetime.now(), user_id)
            )
            conn.commit()
            
            return True
        else:
            print(f"❌ ユーザー '{username}' のパスワードが間違っています")
            return False
            
    except Exception as e:
        print(f"❌ ログインテストでエラーが発生: {e}")
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def test_all_users():
    """すべてのテストユーザーでログインテスト"""
    test_users = [
        {"username": "admin_test", "password": "admin123"},
        {"username": "normal_test", "password": "normal123"},
        {"username": "guest_test", "password": "guest123"}
    ]
    
    print("=" * 50)
    print("テストユーザーログインテスト")
    print("=" * 50)
    
    for user_info in test_users:
        print(f"\n--- {user_info['username']} ---")
        test_login(user_info["username"], user_info["password"])
    
    # 間違ったパスワードのテスト
    print(f"\n--- 間違ったパスワードのテスト ---")
    test_login("admin_test", "wrong_password")
    
    print("\n" + "=" * 50)
    print("テスト完了")
    print("=" * 50)

if __name__ == "__main__":
    test_all_users()
