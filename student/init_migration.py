#!/usr/bin/env python3
"""
Student Service Migration Initialization Script
マイグレーション用のファイルを初期化
"""

import os
import sys
import time
from flask import Flask
from flask_migrate import Migrate, init, migrate as flask_migrate, upgrade

def init_migration():
    """マイグレーション環境を初期化"""
    
    # アプリケーションファクトリーを使用
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from app import create_app
    
    # アプリケーション作成
    app = create_app()
    
    with app.app_context():
        # 全てのモデルがインポートされていることを確認
        from app import models
        print(f"Loaded models: {models.__all__}")
        
        # データベース接続確認
        from app.database import db
        try:
            # 簡単な接続テスト - データベースに接続できるかテスト
            db.create_all()
            print("Database connection successful")
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
        
        # migrations フォルダが存在しない場合は初期化
        if not os.path.exists('migrations'):
            print("Initializing migration repository...")
            init()
            print("Migration repository initialized. Waiting for files to be created...")
            time.sleep(3)  # ファイル作成を待機
        
        # env.pyファイルが存在することを確認してからマイグレーション作成
        if os.path.exists('migrations/env.py'):
            print("Creating initial migration...")
            flask_migrate(message='Initial migration for student service')
            print("Applying migrations to database...")
            upgrade()
            print("Migration completed successfully!")
        else:
            print("Warning: Migration repository not properly initialized. Skipping migration creation.")
            return False
        
        print("Student service migration initialization completed!")
        return True

if __name__ == "__main__":
    success = init_migration()
    if success:
        print("Migration initialization completed successfully")
    else:
        print("Migration initialization failed, but continuing...")
    # Always exit with success to allow the server to start
    sys.exit(0)
