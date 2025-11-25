from flask import Flask, request
from flask_socketio import SocketIO
import os
import logging
import psycopg2
from psycopg2 import sql
import sys
import traceback

socketio = SocketIO(cors_allowed_origins="*", async_mode="gevent")

import logging
import sys
import traceback

# ログ設定
logger = logging.getLogger(__name__)

def create_app():
    try:
        logger.info("=== Admin Service App Creation Started ===")
        
        app = Flask(__name__)
        logger.info("Flask app instance created")

        # Flask設定
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'admin-secret-key-change-in-production-2024')
        logger.info("Flask secret key configured")

        # ログ設定
        log_dir = "/app/logs"
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(log_dir, "access.log"),
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
        )
        logger.info("Logging configured")

        @app.before_request
        def log_request_info():
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            path = request.path
            logging.info(f"IP: {ip} - Path: /admin{path}")

        # DB設定
        app.config["POSTGRES_HOST"] = os.getenv("POSTGRES_HOST", "postgres")
        app.config["POSTGRES_DB"] = os.getenv("POSTGRES_DB", "mydb")
        app.config["POSTGRES_USER"] = os.getenv("POSTGRES_USER", "user")
        app.config["POSTGRES_PASSWORD"] = os.getenv("POSTGRES_PASSWORD", "pass")
        app.config["REDIS_HOST"] = os.getenv("REDIS_HOST", "redis")
        logger.info("Database configuration loaded")

        # データベース初期化
        logger.info("Initializing database...")
        from app.database import init_db
        init_db(app)
        logger.info("Database initialized")

        # マイグレーション実行
        logger.info("Performing migration...")
        with app.app_context():
            perform_migration(app)
        logger.info("Migration completed")

        # モデルをインポート（マイグレーションで必要）
        logger.info("Importing models...")
        from app import models
        logger.info("Models imported")

        # モデルに定義されたBlueprintを自動登録
        logger.info("Registering model blueprints...")
        models.register_model_blueprints(app)
        logger.info("Model blueprints registered")

        logger.info("Registering route blueprints...")
        from app import routes
        routes.register_blueprints(app)
        logger.info("Route blueprints registered")
        # エラーハンドラーを登録
        logger.info("Registering error handlers...")
        from app.utils.error_handlers import register_error_handlers
        register_error_handlers(app)
        logger.info("Error handlers registered")

        # デバッグ用：登録されているルートを表示
        def debug_routes():
            print("=== 登録されているルート ===")
            for rule in app.url_map.iter_rules():
                methods = [m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]
                print(f"{rule.endpoint}: {rule.rule} [{', '.join(methods)}]")
                
                # login関連のルートを特に詳しく表示
                if 'login' in rule.rule.lower() or 'login' in rule.endpoint.lower():
                    print(f"  *** LOGIN ROUTE DETECTED ***")
                    print(f"  Endpoint: {rule.endpoint}")
                    print(f"  Rule: {rule.rule}")
                    print(f"  Methods: {rule.methods}")
                    print(f"  Defaults: {rule.defaults}")
            print("========================")
        
        # アプリケーション起動時にルートをデバッグ表示
        with app.app_context():
            debug_routes()

        logger.info("Initializing SocketIO...")
        socketio.init_app(app)
        logger.info("SocketIO initialized")
        
        # WebSocket統計情報ブロードキャスターを開始
        try:
            from app.routes.ws import start_statistics_broadcaster
            start_statistics_broadcaster()
            logger.info("Statistics broadcaster started")
        except Exception as e:
            logger.warning(f"Failed to start statistics broadcaster: {e}")
        
        # 最終テーブル確認（起動時の最後のチェック）
        logger.info("Final table verification...")
        with app.app_context():
            ensure_tables_on_startup(app)
        logger.info("Final table verification completed")
        
        logger.info("=== Admin Service App Creation Completed Successfully ===")
        return app
        
    except Exception as e:
        logger.error(f"=== Admin Service App Creation Failed ===")
        logger.error(f"Error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def perform_migration(app):
    """スマートマイグレーションを実行：改善版（トランザクション問題を解決）"""
    conn = None
    cursor = None
    
    try:
        logger.info("Admin service: Starting migration check...")
        
        # 単純なテーブル存在チェックのみ実行（トランザクション問題を回避）
        conn = psycopg2.connect(
            host=app.config["POSTGRES_HOST"],
            database=app.config["POSTGRES_DB"],
            user=app.config["POSTGRES_USER"],
            password=app.config["POSTGRES_PASSWORD"],
            options='-c client_encoding=utf8'
        )
        # オートコミットモードを有効にしてトランザクション問題を回避
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 必要なテーブルリスト
        required_tables = ['users', 'permissions']
        missing_tables = []
        
        # 各テーブルの存在をチェック
        for table_name in required_tables:
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, (table_name,))
                
                result = cursor.fetchone()
                table_exists = result[0] if result else False
                
                if not table_exists:
                    missing_tables.append(table_name)
                    logger.info(f"Admin service: Table '{table_name}' does not exist")
                else:
                    logger.info(f"Admin service: Table '{table_name}' exists")
                    
            except Exception as e:
                logger.warning(f"Admin service: Error checking table '{table_name}': {e}")
                missing_tables.append(table_name)
        
        # テーブルが不足している場合は直接作成
        if missing_tables:
            logger.info(f"Admin service: Missing tables: {missing_tables}")
            logger.info("Admin service: Creating tables directly via SQLAlchemy...")
            _create_tables_directly(app)
        else:
            logger.info("Admin service: All required tables exist. No migration needed.")
        
    except Exception as e:
        logger.error(f"Admin service: Migration error: {e}")
        logger.warning("Admin service: Falling back to direct table creation...")
        try:
            _create_tables_directly(app)
        except Exception as fallback_error:
            logger.error(f"Admin service: Fallback table creation failed: {fallback_error}")
            raise
    finally:
        # リソースのクリーンアップ
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as cleanup_error:
            logger.warning(f"Admin service: Cleanup error: {cleanup_error}")



def _create_tables_directly(app):
    """SQLAlchemyを使用してテーブルを直接作成（改善版）"""
    try:
        from app.database import db
        
        with app.app_context():
            logger.info("Admin service: Creating tables using SQLAlchemy...")
            
            # セッションをクリアして新しい状態で開始
            try:
                db.session.remove()
            except:
                pass
            
            # テーブル作成
            db.create_all()
            
            # 作成結果を確認
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            created_tables = inspector.get_table_names()
            logger.info(f"Admin service: Available tables after creation: {created_tables}")
            
            # 必要なテーブルが作成されたか確認
            required_tables = ['users', 'permissions']
            missing = [t for t in required_tables if t not in created_tables]
            if missing:
                logger.warning(f"Admin service: Still missing tables after creation: {missing}")
            else:
                logger.info("Admin service: All required tables created successfully")
            
            # コミット
            db.session.commit()
            logger.info("Admin service: Database changes committed")
            
    except Exception as e:
        logger.error(f"Admin service: Direct table creation failed: {e}")
        # セッションをロールバック
        try:
            from app.database import db
            db.session.rollback()
        except:
            pass
        raise

def _insert_default_permissions():
    """デフォルト権限データの挿入（簡略版）"""
    try:
        logger.info("Admin service: Skipping default permissions insertion for now...")
        # 現在はスキップ - テーブル作成が安定してから後で実装
        pass
    except Exception as e:
        logger.warning(f"Admin service: Failed to insert default permissions: {e}")

def ensure_tables_on_startup(app):
    """
    アプリケーション起動時にテーブルの存在を確認し、必要に応じて作成する
    """
    try:
        from app.database import db
        from app.utils.auto_repair import ensure_tables_exist, force_create_tables
        from sqlalchemy import inspect
        
        with app.app_context():
            logger.info("🔧 Performing startup table verification...")
            
            # テーブル存在確認
            if not ensure_tables_exist():
                logger.warning("⚠️  Initial table verification failed, attempting force creation...")
                if force_create_tables():
                    logger.info("✅ Force table creation succeeded")
                else:
                    logger.error("❌ Force table creation failed")
                    
            # 最終確認
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"✅ Startup verification completed. Available tables: {tables}")
            
            # 各テーブルの動作確認
            try:
                from app.models.user import User
                from app.models.permission import Permission
                
                user_count = User.query.count()
                permission_count = Permission.query.count()
                logger.info(f"✅ Table operation test - Users: {user_count}, Permissions: {permission_count}")
            except Exception as test_error:
                logger.warning(f"⚠️  Table operation test failed: {test_error}")
                # 再度強制作成
                logger.info("🚨 Attempting emergency table recreation...")
                force_create_tables()
                
    except Exception as e:
        logger.error(f"❌ Startup table verification failed: {e}")
        # 最後の手段として直接作成を試行
        try:
            from app.database import db
            with app.app_context():
                db.create_all()
                logger.info("✅ Emergency db.create_all() completed")
        except Exception as emergency_error:
            logger.error(f"❌ Emergency table creation failed: {emergency_error}")
