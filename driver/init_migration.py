#!/usr/bin/env python3
"""
Driver Service Migration Initialization Script
マイグレーション用のファイルを初期化
"""

import os
import sys
import time
import shutil
from flask import Flask
from flask_migrate import Migrate, init, migrate as flask_migrate, upgrade, stamp
from sqlalchemy import text

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
        try:
            # 既存のマイグレーション履歴を確認
            print("Checking existing migration state...")
            
            # データベース接続テスト
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                print("Database connection successful")
            except Exception as e:
                print(f"Database connection failed: {e}")
                print("Waiting for database to be ready...")
                time.sleep(10)
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                print("Database connection established")
            
            # Alembicバージョンテーブルの存在確認
            try:
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                has_alembic_table = 'alembic_version' in tables
                print(f"Alembic version table exists: {has_alembic_table}")
            except Exception as e:
                print(f"Could not check alembic table: {e}")
                has_alembic_table = False
            
            # マイグレーション戦略の決定
            migrations_exist = os.path.exists('migrations')
            env_py_exists = os.path.exists('migrations/env.py')
            
            print(f"Migrations directory exists: {migrations_exist}")
            print(f"env.py exists: {env_py_exists}")
            
            if not migrations_exist or not env_py_exists or has_alembic_table:
                # 新規初期化が必要（alembic_tableが存在する場合も含む）
                print("Performing fresh migration initialization...")
                
                # Alembicテーブルをクリア
                if has_alembic_table:
                    print("Clearing alembic version table...")
                    try:
                        with db.engine.connect() as conn:
                            conn.execute(text("DELETE FROM alembic_version"))
                            conn.commit()
                        print("Alembic version table cleared")
                    except Exception as e:
                        print(f"Could not clear alembic table: {e}")
                
                if migrations_exist:
                    print("Removing existing migrations directory...")
                    shutil.rmtree('migrations')
                
                print("Initializing migration repository...")
                init()
                time.sleep(2)
                
                print("Creating initial migration...")
                flask_migrate(message='Initial migration for driver service')
                
                print("Applying migrations to database...")
                upgrade()
                
            else:
                # 既存のマイグレーション環境での処理
                print("Existing migration environment detected")
                
                try:
                    # マイグレーション状態の確認
                    print("Attempting to upgrade existing migrations...")
                    upgrade()
                    print("Migration upgrade successful")
                    
                except Exception as migration_error:
                    print(f"Migration upgrade failed: {migration_error}")
                    
                    # マイグレーション履歴の不整合を解決
                    print("Attempting to resolve migration conflicts...")
                    
                    if has_alembic_table:
                        # Alembicテーブルをクリア
                        print("Clearing alembic version table...")
                        try:
                            with db.engine.connect() as conn:
                                conn.execute(text("DELETE FROM alembic_version"))
                                conn.commit()
                            print("Alembic version table cleared")
                        except Exception as e:
                            print(f"Could not clear alembic table: {e}")
                    
                    # マイグレーションディレクトリを再作成
                    print("Recreating migration environment...")
                    shutil.rmtree('migrations')
                    
                    print("Reinitializing migration repository...")
                    init()
                    time.sleep(2)
                    
                    # 既存のテーブル構造をベースラインとして使用
                    print("Creating baseline migration from existing schema...")
                    flask_migrate(message='Baseline migration from existing schema')
                    
                    # ベースラインとしてマーク（実際のマイグレーションは実行しない）
                    print("Marking as baseline migration...")
                    stamp()
                    
                    print("Migration environment recreated successfully")
                    
        except Exception as e:
            print(f"Migration initialization failed: {e}")
            print("Falling back to direct table creation...")
            
            # 直接テーブル作成
            try:
                print("Creating tables using SQLAlchemy...")
                db.create_all()
                print("✅ Tables created successfully using SQLAlchemy")
                
                # テーブルが正しく作成されたか確認
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                table_names = inspector.get_table_names()
                print(f"✅ Created tables: {table_names}")
                
                # 各モデルのテーブル存在確認
                from app.models import Driver
                try:
                    driver_count = Driver.query.count()
                    print(f"✅ Drivers table: {driver_count} records")
                except Exception as query_error:
                    print(f"⚠️  Table query test failed: {query_error}")
                    
            except Exception as create_error:
                print(f"❌ Direct table creation failed: {create_error}")
                print("Attempting emergency table creation...")
                
                # 緊急措置：個別にテーブル作成を試行
                try:
                    # まずデータベース接続を確認
                    with db.engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                        print("✅ Database connection is working")
                    
                    # 個別にモデルのテーブルを作成
                    from app.models import Driver
                    Driver.__table__.create(db.engine, checkfirst=True)
                    print("✅ Individual table creation succeeded")
                    
                except Exception as emergency_error:
                    print(f"❌ Emergency table creation failed: {emergency_error}")
                    sys.exit(1)
        
        print("Driver service migration initialization completed!")

if __name__ == "__main__":
    init_migration()
