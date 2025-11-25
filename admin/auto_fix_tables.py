#!/usr/bin/env python3
"""
Admin Service - Automatic Table Creation and Repair Script
テーブルが存在しない場合に自動的に作成する緊急修復スクリプト
"""

import os
import sys
from flask import Flask
from sqlalchemy import text

def auto_fix_tables():
    """テーブルの存在確認と自動修復"""
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
    
    # SQLAlchemy 初期化
    from app.database import db
    db.init_app(app)
    
    # モデルをインポート
    from app import models
    
    with app.app_context():
        try:
            print("🔧 Admin Service - Auto Fix Tables")
            print("=" * 50)
            
            # データベース接続テスト
            print("📡 Testing database connection...")
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # 既存のテーブルを確認
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"📋 Existing tables: {existing_tables}")
            
            # 必要なテーブルのリスト
            required_tables = ['users', 'permissions']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if not missing_tables:
                print("✅ All required tables exist")
                
                # テーブルの動作確認
                from app.models import User, Permission
                user_count = User.query.count()
                permission_count = Permission.query.count()
                print(f"✅ Users table: {user_count} records")
                print(f"✅ Permissions table: {permission_count} records")
                
            else:
                print(f"⚠️  Missing tables: {missing_tables}")
                print("🔧 Creating missing tables...")
                
                # 全テーブルを作成
                db.create_all()
                print("✅ Tables created using db.create_all()")
                
                # 再度確認
                inspector = inspect(db.engine)
                updated_tables = inspector.get_table_names()
                print(f"📋 Updated tables: {updated_tables}")
                
                # 動作確認
                from app.models import User, Permission
                user_count = User.query.count()
                permission_count = Permission.query.count()
                print(f"✅ Users table: {user_count} records")
                print(f"✅ Permissions table: {permission_count} records")
            
            print("=" * 50)
            print("🎉 Admin Service tables are ready!")
            return True
            
        except Exception as e:
            print(f"❌ Auto fix failed: {e}")
            
            # 最後の手段：個別テーブル作成
            try:
                print("🚨 Attempting emergency table creation...")
                from app.models import User, Permission
                
                # 個別にテーブルを作成
                User.__table__.create(db.engine, checkfirst=True)
                Permission.__table__.create(db.engine, checkfirst=True)
                print("✅ Emergency table creation succeeded")
                return True
                
            except Exception as emergency_error:
                print(f"❌ Emergency table creation failed: {emergency_error}")
                return False

if __name__ == "__main__":
    success = auto_fix_tables()
    sys.exit(0 if success else 1)