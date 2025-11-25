#!/usr/bin/env python3
"""
管理者テストユーザー作成スクリプト
"""

import sys
import os
sys.path.insert(0, '/app')

from app.models.user import User
from app.database import db
from app.utils.auth_utils import PasswordManager
import psycopg2
from psycopg2 import sql

def create_test_admin():
    """テスト用管理者を作成"""
    try:
        # データベース接続設定
        db_config = {
            'host': os.getenv('POSTGRES_HOST', 'postgres'),
            'database': os.getenv('POSTGRES_DB', 'mydb'),
            'user': os.getenv('POSTGRES_USER', 'user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'pass')
        }
        
        # データベースに直接接続
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # 既存の管理者をチェック
        cur.execute("SELECT username FROM users WHERE username = %s", ('admin_test',))
        existing = cur.fetchone()
        
        if not existing:
            # パスワードとsaltを生成
            salt, password_hash = PasswordManager.hash_password('admin123')
            
            cur.execute("""
                INSERT INTO users (username, email, password_hash, password_salt, role, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                'admin_test',
                'admin@test.com',
                password_hash,
                salt,
                'admin',
                True
            ))
            
            conn.commit()
            print("Test admin created: admin_test / admin123")
        else:
            print("Test admin already exists")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating test admin: {e}")

if __name__ == "__main__":
    create_test_admin()
