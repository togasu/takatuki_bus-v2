#!/usr/bin/env python3
"""
Runtime Auto Repair for Admin Service (Improved Version)
実行時にテーブル不存在エラーが発生した際の自動修復機能（改善版）
"""

import logging
from functools import wraps
from sqlalchemy.exc import ProgrammingError
from psycopg2.errors import UndefinedTable
from flask import current_app
import psycopg2

logger = logging.getLogger(__name__)

def auto_repair_on_table_error(f):
    """
    テーブル不存在エラーが発生した際に自動的にテーブルを作成するデコレータ
    トランザクション問題を完全に回避する新しいアプローチ
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ProgrammingError as e:
            # UndefinedTableエラーの場合のみ処理
            if isinstance(e.orig, UndefinedTable) or "relation" in str(e) and "does not exist" in str(e):
                current_app.logger.warning(f"Table not found error detected: {e}")
                current_app.logger.info("Attempting automatic table creation...")
                
                try:
                    # 完全に新しいPostgreSQLセッションで修復を実行
                    success = create_missing_tables_external()
                    
                    if success:
                        current_app.logger.info("✅ Automatic table creation completed")
                        # アプリケーションを再起動させる（最も確実な方法）
                        current_app.logger.warning("🔄 Please restart the application to complete the repair")
                        return {"error": "Tables were missing but have been created. Please retry your request.", "status": "repaired"}, 503
                    else:
                        current_app.logger.error("❌ Automatic table repair failed")
                        return {"error": "Database tables are missing and repair failed", "status": "error"}, 500
                        
                except Exception as repair_error:
                    current_app.logger.error(f"❌ Automatic table repair failed: {repair_error}")
                    return {"error": f"Database repair failed: {str(repair_error)}", "status": "error"}, 500
            else:
                raise e
        except Exception as e:
            # その他のエラーはそのまま再発生
            raise e
    
    return decorated_function

def create_missing_tables_external():
    """
    外部PostgreSQL接続を使用してテーブルを作成
    Flaskアプリのセッション問題を完全に回避
    """
    try:
        # Flaskアプリの設定を取得
        db_config = {
            'host': current_app.config.get("POSTGRES_HOST", "postgres"),
            'database': current_app.config.get("POSTGRES_DB", "bus_admin"),
            'user': current_app.config.get("POSTGRES_USER", "admin"),
            'password': current_app.config.get("POSTGRES_PASSWORD", "pass")
        }
        
        # 新しい接続を作成（オートコミット有効）
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # テーブル存在確認
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('users', 'permissions')
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        current_app.logger.info(f"Existing tables: {existing_tables}")
        
        # usersテーブル作成
        if 'users' not in existing_tables:
            current_app.logger.info("Creating users table...")
            cursor.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(80) NOT NULL UNIQUE,
                    email VARCHAR(120) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    password_salt VARCHAR(255),
                    role VARCHAR(20) DEFAULT 'normal',
                    is_active BOOLEAN DEFAULT true,
                    last_login TIMESTAMP,
                    last_logout TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            current_app.logger.info("✅ Users table created")
        
        # permissionsテーブル作成
        if 'permissions' not in existing_tables:
            current_app.logger.info("Creating permissions table...")
            cursor.execute("""
                CREATE TABLE permissions (
                    id SERIAL PRIMARY KEY,
                    resource VARCHAR(100) NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    is_allowed BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(resource, action, role)
                )
            """)
            current_app.logger.info("✅ Permissions table created")
        
        # 作成結果を確認
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('users', 'permissions')
        """)
        final_tables = [row[0] for row in cursor.fetchall()]
        current_app.logger.info(f"Tables after creation: {final_tables}")
        
        cursor.close()
        conn.close()
        
        # 成功判定
        return len(final_tables) >= 2
        
    except Exception as e:
        current_app.logger.error(f"External table creation failed: {e}")
        return False

def ensure_tables_exist():
    """
    テーブルの存在を確認する簡単な関数
    """
    try:
        from app.database import db
        from sqlalchemy import inspect
        
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        required_tables = ['users', 'permissions']
        
        missing = [t for t in required_tables if t not in existing_tables]
        if missing:
            current_app.logger.warning(f"Missing tables: {missing}")
            return False
        
        current_app.logger.info(f"✅ All required tables exist: {existing_tables}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Table existence check failed: {e}")
        return False

def force_create_tables():
    """
    強制的にテーブルを作成
    """
    try:
        from app.database import db
        
        # セッションクリア
        try:
            db.session.remove()
        except:
            pass
        
        # テーブル作成
        db.create_all()
        
        # 確認
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        created_tables = inspector.get_table_names()
        current_app.logger.info(f"✅ Tables created: {created_tables}")
        
        return 'users' in created_tables and 'permissions' in created_tables
    
    except Exception as e:
        current_app.logger.error(f"Force table creation failed: {e}")
        return False

def repair_tables_manually():
    """
    手動でテーブル修復を実行する関数
    api.pyからの呼び出し用
    """
    try:
        current_app.logger.info("🔧 Manual table repair requested...")
        
        # 外部PostgreSQL接続での修復を試行
        success = create_missing_tables_external()
        
        if success:
            current_app.logger.info("✅ Manual table repair completed")
            return True
        else:
            # フォールバック：SQLAlchemy経由での作成
            current_app.logger.warning("⚠️ External repair failed, trying SQLAlchemy fallback...")
            return force_create_tables()
            
    except Exception as e:
        current_app.logger.error(f"❌ Manual table repair failed: {e}")
        return False