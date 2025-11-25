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
        logger.info("=== Driver Service App Creation Started ===")
        
        app = Flask(__name__, static_url_path='/driver/static')
        logger.info("Flask app instance created with static_url_path='/driver/static'")

        # Flask設定
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'driver-secret-key-change-in-production-2024')
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
            logging.info(f"IP: {ip} - Path: /driver{path}")

        @app.context_processor
        def inject_url_vars():
            """テンプレートで使用するURL変数を注入"""
            return dict(base_url='/driver')

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

        # WebSocket初期化
        logger.info("Initializing WebSocket...")
        socketio.init_app(app)
        logger.info("WebSocket initialized")

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
        
        debug_routes()
        
        # アプリケーションが正常に作成されたことをログに記録
        logger.info(f"Driver service app is ready. App type: {type(app)}")
        
        return app
        
    except Exception as e:
        logger.error(f"Failed to create driver service application: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

def perform_migration(app):
    """スマートマイグレーションを実行：改善版（トランザクション問題を解決）"""
    conn = None
    cursor = None
    
    try:
        logger.info("Driver service: Starting migration check...")
        
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
        
        # 必要なテーブルリスト（ドライバーサービス用）
        required_tables = ['drivers', 'qa']
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
                    logger.info(f"Driver service: Table '{table_name}' does not exist")
                else:
                    logger.info(f"Driver service: Table '{table_name}' exists")
                    
            except Exception as e:
                logger.warning(f"Driver service: Error checking table '{table_name}': {e}")
                missing_tables.append(table_name)
        
        # テーブルが不足している場合は直接作成
        if missing_tables:
            logger.info(f"Driver service: Missing tables: {missing_tables}")
            logger.info("Driver service: Creating tables directly via SQLAlchemy...")
            _create_tables_directly(app)
        else:
            logger.info("Driver service: All required tables exist. No migration needed.")
        
    except Exception as e:
        logger.error(f"Driver service: Migration error: {e}")
        logger.warning("Driver service: Falling back to direct table creation...")
        try:
            _create_tables_directly(app)
        except Exception as fallback_error:
            logger.error(f"Driver service: Fallback table creation failed: {fallback_error}")
            raise
    finally:
        # リソースのクリーンアップ
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as cleanup_error:
            logger.warning(f"Driver service: Cleanup error: {cleanup_error}")

def _create_tables_directly(app):
    """SQLAlchemyを使用してテーブルを直接作成（改善版）"""
    try:
        from app.database import db
        
        with app.app_context():
            logger.info("Driver service: Creating tables using SQLAlchemy...")
            
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
            logger.info(f"Driver service: Available tables after creation: {created_tables}")
            
            # 必要なテーブルが作成されたか確認
            required_tables = ['drivers', 'qa']
            missing = [t for t in required_tables if t not in created_tables]
            if missing:
                logger.warning(f"Driver service: Still missing tables after creation: {missing}")
            else:
                logger.info("Driver service: All required tables created successfully")
            
            # コミット
            db.session.commit()
            logger.info("Driver service: Database changes committed")
            
    except Exception as e:
        logger.error(f"Driver service: Direct table creation failed: {e}")
        # セッションをロールバック
        try:
            from app.database import db
            db.session.rollback()
        except:
            pass
        raise
