#!/usr/bin/env python3
"""
Runtime Auto Repair for Admin Service
実行時にテーブル不存在エラーが発生した際の自動修復機能
"""

import logging
from functools import wraps
from sqlalchemy.exc import ProgrammingError
from psycopg2.errors import UndefinedTable
from flask import current_app

logger = logging.getLogger(__name__)

def auto_repair_on_table_error(f):
    """
    テーブル不存在エラーが発生した際に自動的にテーブルを作成するデコレータ（改善版）
    PostgreSQLのトランザクション状態の問題を解決
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
                    # 完全に新しいセッションで修復を実行
                    success = force_create_tables_new_session()
                    
                    if success:
                        current_app.logger.info("✅ Automatic table creation completed")
                        # 新しいセッションで元の関数を再実行
                        current_app.logger.info("Retrying original function after table repair...")
                        return f(*args, **kwargs)
                    else:
                        current_app.logger.error("❌ Automatic table repair failed")
                        raise e
                        
                except Exception as repair_error:
                    current_app.logger.error(f"❌ Automatic table repair failed: {repair_error}")
                    raise e
            else:
                raise e
        except Exception as e:
            # その他のエラーはそのまま再発生
            raise e
    
    return decorated_function
                        
                        # 作成後の確認
                        inspector = inspect(db.engine)
                        updated_tables = inspector.get_table_names()
                        current_app.logger.info(f"✅ Tables after repair: {updated_tables}")
                        
                        # データベース接続の確認
                        conn.execute(text("SELECT 1"))
                        current_app.logger.info("✅ Database connection verified")
                    
                    # セッションを新しく開始
                    try:
                        db.session.remove()
                        current_app.logger.info("Database session refreshed")
                    except Exception as session_error:
                        current_app.logger.warning(f"Session refresh warning: {session_error}")
                    
                    # 再度元の関数を実行
                    current_app.logger.info("Retrying original function after table repair...")
                    return f(*args, **kwargs)
                    
                except Exception as repair_error:
                    current_app.logger.error(f"❌ Automatic table repair failed: {repair_error}")
                    
                    # 最後の手段：セッションをクリアして再試行
                    try:
                        db.session.rollback()
                        db.session.remove()
                        current_app.logger.info("Session cleared for final retry")
                        return f(*args, **kwargs)
                    except Exception as final_error:
                        current_app.logger.error(f"❌ Final retry also failed: {final_error}")
                    
                    # 修復に失敗した場合は元のエラーを再発生
                    raise e
            else:
                # その他のProgrammingErrorは再発生
                raise e
        except Exception as other_error:
            # その他のエラーは通常通り処理
            raise other_error
    
    return decorated_function


def repair_tables_manually():
    """
    手動でテーブル修復を実行する関数
    """
    try:
        from app.database import db
        from sqlalchemy import inspect, text
        from app.models import User, Permission
        
        current_app.logger.info("🔧 Manual table repair initiated...")
        
        # 完全に新しいセッションで作業
        with db.engine.connect() as conn:
            # テーブル状況確認
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            current_app.logger.info(f"📋 Current tables: {existing_tables}")
            
            # 必要なテーブルがあるかチェック
            required_tables = ['users', 'permissions']
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                current_app.logger.info(f"⚠️  Missing tables: {missing_tables}")
                
                # テーブル作成
                db.create_all()
                current_app.logger.info("✅ Tables created")
                
                # 再確認
                inspector = inspect(db.engine)
                updated_tables = inspector.get_table_names()
                current_app.logger.info(f"✅ Updated tables: {updated_tables}")
            else:
                current_app.logger.info("✅ All required tables exist")
            
            # データベース接続テスト
            conn.execute(text("SELECT 1"))
            current_app.logger.info("✅ Database connection test passed")
            
        return True
        
    except Exception as e:
        current_app.logger.error(f"❌ Manual table repair failed: {e}")
        return False

def ensure_tables_exist():
    """
    テーブルが存在することを確認し、存在しない場合は作成する
    """
    try:
        from app.database import db
        from sqlalchemy import inspect
        
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = ['users', 'permissions']
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.warning(f"Missing tables detected: {missing_tables}")
            logger.info("Creating missing tables...")
            
            db.create_all()
            
            # 再確認
            inspector = inspect(db.engine)
            updated_tables = inspector.get_table_names()
            logger.info(f"✅ Tables created successfully: {updated_tables}")
            
            return True
        else:
            logger.info(f"✅ All required tables exist: {existing_tables}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Table verification failed: {e}")
        return False

def force_create_tables():
    """
    強制的にテーブルを作成する（緊急時用）
    """
    try:
        from app.database import db
        logger.info("🚨 Force creating all tables...")
        
        db.create_all()
        logger.info("✅ Force table creation completed")
        
        # 結果確認
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        logger.info(f"✅ Available tables after force creation: {tables}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Force table creation failed: {e}")
        return False