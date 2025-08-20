#!/usr/bin/env python3
"""
Driver Service Migration Initialization Script
マイグレーション用のファイルを初期化
"""

import os
import sys
import time
from flask import Flask
from flask_migrate import Migrate, init, migrate as flask_migrate, upgrade

def init_migration():
    """マイグレーション環境を初期化"""
    app = Flask(__name__)
    
    # 環境変数から設定を読み込み
    app.config["POSTGRES_HOST"] = os.getenv("POSTGRES_HOST", "postgres")
    app.config["POSTGRES_DB"] = os.getenv("POSTGRES_DB", "mydb")
    app.config["POSTGRES_USER"] = os.getenv("POSTGRES_USER", "user")
    app.config["POSTGRES_PASSWORD"] = os.getenv("POSTGRES_PASSWORD", "pass")
    
    # データベース設定
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql://{app.config['POSTGRES_USER']}:"
        f"{app.config['POSTGRES_PASSWORD']}@"
        f"{app.config['POSTGRES_HOST']}/"
        f"{app.config['POSTGRES_DB']}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # SQLAlchemy とマイグレーション初期化
    from app.database import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    
    # モデルをインポート
    from app import models
    
    with app.app_context():
        # migrations フォルダが存在しない場合は初期化
        if not os.path.exists('migrations'):
            print("Initializing migration repository...")
            init()
            print("Migration repository initialized. Waiting for files to be created...")
            time.sleep(2)  # ファイル作成を待機
        
        # env.pyファイルが存在することを確認してからマイグレーション作成
        if os.path.exists('migrations/env.py'):
            print("Creating initial migration...")
            flask_migrate(message='Initial migration for driver service')
            print("Applying migrations to database...")
            upgrade()
        else:
            print("Warning: Migration repository not properly initialized. Skipping migration creation.")
        
        print("Driver service migration initialization completed!")

if __name__ == "__main__":
    init_migration()
