#!/usr/bin/env python3
"""
直接SQLを使ってテスト用ユーザーを作成するスクリプト
"""

import psycopg2
import bcrypt
import os
from datetime import datetime

def hash_password(password):
    """パスワードをハッシュ化"""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return salt.decode('utf-8'), password_hash.decode('utf-8')

def create_test_users():
    """テスト用ユーザーを作成"""
    # データベース接続設定
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'postgres'),
        'database': os.getenv('POSTGRES_DB', 'mydb'),
        'user': os.getenv('POSTGRES_USER', 'user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'pass'),
        'port': 5432
    }
    
    try:
        # データベースに接続
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # テストユーザーのデータ
        test_users = [
            {
                "username": "admin_test",
                "email": "admin@test.com",
                "password": "admin123",
                "role": "admin"
            },
            {
                "username": "normal_test",
                "email": "normal@test.com", 
                "password": "normal123",
                "role": "normal"
            },
            {
                "username": "guest_test",
                "email": "guest@test.com",
                "password": "guest123", 
                "role": "guest"
            }
        ]
        
        for user_data in test_users:
            # 既存のユーザーをチェック
            cur.execute(
                "SELECT id FROM users WHERE username = %s",
                (user_data["username"],)
            )
            
            if cur.fetchone():
                print(f"ユーザー '{user_data['username']}' は既に存在します。")
                continue
            
            # パスワードをハッシュ化
            salt, password_hash = hash_password(user_data["password"])
            
            # ユーザーを挿入
            cur.execute(
                """
                INSERT INTO users (username, email, password_hash, password_salt, role, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_data["username"],
                    user_data["email"],
                    password_hash,
                    salt,
                    user_data["role"],
                    True,
                    datetime.now(),
                    datetime.now()
                )
            )
            
            print(f"テストユーザー '{user_data['username']}' を作成しました。")
        
        # 変更をコミット
        conn.commit()
        print("すべてのテストユーザーの作成が完了しました。")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def list_users():
    """現在のユーザー一覧を表示"""
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'postgres'),
        'database': os.getenv('POSTGRES_DB', 'mydb'),
        'user': os.getenv('POSTGRES_USER', 'user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'pass'),
        'port': 5432
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        cur.execute("SELECT id, username, email, role, is_active, created_at FROM users ORDER BY id")
        users = cur.fetchall()
        
        print("\n現在のユーザー一覧:")
        print("-" * 80)
        print(f"{'ID':<5} {'ユーザー名':<15} {'メール':<25} {'ロール':<10} {'有効':<5} {'作成日':<20}")
        print("-" * 80)
        
        for user in users:
            user_id, username, email, role, is_active, created_at = user
            active_str = '○' if is_active else '×'
            created_str = created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else 'なし'
            print(f"{user_id:<5} {username:<15} {email:<25} {role:<10} {active_str:<5} {created_str:<20}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def delete_test_users():
    """テストユーザーを削除"""
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'postgres'),
        'database': os.getenv('POSTGRES_DB', 'mydb'),
        'user': os.getenv('POSTGRES_USER', 'user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'pass'),
        'port': 5432
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        test_usernames = ["admin_test", "normal_test", "guest_test"]
        
        for username in test_usernames:
            cur.execute("DELETE FROM users WHERE username = %s", (username,))
            if cur.rowcount > 0:
                print(f"テストユーザー '{username}' を削除しました。")
            else:
                print(f"テストユーザー '{username}' は見つかりませんでした。")
        
        conn.commit()
        print("テストユーザーの削除が完了しました。")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

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
            print("使用方法: python create_test_users_sql.py [create|list|delete]")
    else:
        print("テストユーザーを作成します...")
        create_test_users()
        print("\n作成後のユーザー一覧:")
        list_users()
