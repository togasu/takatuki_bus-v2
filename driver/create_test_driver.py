#!/usr/bin/env python3
"""
ドライバーテストユーザー作成スクリプト
"""

import sys
import os
sys.path.insert(0, '/app')

from werkzeug.security import generate_password_hash
import psycopg2
from psycopg2 import sql

def create_test_driver():
    """テスト用ドライバーを作成"""
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
        
        # driversテーブルが存在しない場合は作成
        cur.execute("""
            CREATE TABLE IF NOT EXISTS drivers (
                id SERIAL PRIMARY KEY,
                driver_id VARCHAR(80) UNIQUE NOT NULL,
                name VARCHAR(120) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                phone VARCHAR(20),
                license_number VARCHAR(50),
                license_expiry DATE,
                hire_date DATE,
                password_hash VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 既存のドライバーをチェック
        cur.execute("SELECT driver_id FROM drivers WHERE driver_id = %s", ('driver_test',))
        existing = cur.fetchone()
        
        if not existing:
            # テスト用ドライバーを作成
            password_hash = generate_password_hash('driver123')
            
            cur.execute("""
                INSERT INTO drivers (driver_id, name, email, phone, license_number, license_expiry, hire_date, password_hash, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                'driver_test',
                'テストドライバー', 
                'driver@test.com',
                '090-1234-5678',
                'TEST-123456789',  # 免許証番号
                '2026-12-31',       # 免許証有効期限
                '2024-01-01',       # 雇用日
                password_hash,
                True
            ))
            
            conn.commit()
            print("Test driver created: driver_test / driver123")
        else:
            print("Test driver already exists")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating test driver: {e}")

if __name__ == "__main__":
    create_test_driver()
