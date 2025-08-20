#!/usr/bin/env python3
"""
直接SQLでテーブル作成とテストユーザー作成
"""

import psycopg2
import bcrypt
import os
from datetime import datetime

def create_tables():
    """テーブルを作成"""
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
        
        # usersテーブル作成
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(80) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                password_salt VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'admin',
                is_active BOOLEAN DEFAULT true,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # permissionsテーブル作成
        cur.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id SERIAL PRIMARY KEY,
                permission_name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                resource VARCHAR(50) NOT NULL,
                action VARCHAR(20) NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        print("テーブルが正常に作成されました。")
        
    except Exception as e:
        print(f"テーブル作成でエラーが発生しました: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def hash_password(password):
    """パスワードをハッシュ化"""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return salt.decode('utf-8'), password_hash.decode('utf-8')

def create_test_users():
    """テスト用ユーザーを作成"""
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

def create_test_permissions():
    """テスト用権限を作成"""
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
        
        # 基本権限
        permissions = [
            {
                "permission_name": "admin_user_read",
                "description": "ユーザー情報の読み取り",
                "resource": "admin_user",
                "action": "read"
            },
            {
                "permission_name": "admin_user_create",
                "description": "ユーザーの作成",
                "resource": "admin_user",
                "action": "create"
            },
            {
                "permission_name": "admin_permission_read",
                "description": "権限情報の読み取り",
                "resource": "admin_permission",
                "action": "read"
            },
            {
                "permission_name": "admin_permission_create",
                "description": "権限の作成",
                "resource": "admin_permission",
                "action": "create"
            }
        ]
        
        for perm_data in permissions:
            # 既存の権限をチェック
            cur.execute(
                "SELECT id FROM permissions WHERE permission_name = %s",
                (perm_data["permission_name"],)
            )
            
            if cur.fetchone():
                print(f"権限 '{perm_data['permission_name']}' は既に存在します。")
                continue
            
            # 権限を挿入
            cur.execute(
                """
                INSERT INTO permissions (permission_name, description, resource, action, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    perm_data["permission_name"],
                    perm_data["description"],
                    perm_data["resource"],
                    perm_data["action"],
                    True,
                    datetime.now()
                )
            )
            
            print(f"権限 '{perm_data['permission_name']}' を作成しました。")
        
        conn.commit()
        print("すべての権限の作成が完了しました。")
        
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

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "tables":
            create_tables()
        elif sys.argv[1] == "users":
            create_test_users()
        elif sys.argv[1] == "permissions":
            create_test_permissions()
        elif sys.argv[1] == "list":
            list_users()
        elif sys.argv[1] == "all":
            create_tables()
            create_test_permissions()
            create_test_users()
            list_users()
        else:
            print("使用方法: python setup_db.py [tables|users|permissions|list|all]")
    else:
        print("データベースとテストデータを初期化します...")
        create_tables()
        create_test_permissions()
        create_test_users()
        list_users()
