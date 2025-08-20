from flask import Flask, request
from flask_socketio import SocketIO
import os
import logging
import psycopg2
from psycopg2 import sql

socketio = SocketIO(cors_allowed_origins="*", async_mode="gevent")

def create_app():
    app = Flask(__name__)

    # ログ設定
    log_dir = "/app/logs"
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(log_dir, "access.log"),
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
    )

    @app.before_request
    def log_request_info():
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        path = request.path
        logging.info(f"IP: {ip} - Path: /driver{path}")

    # DB設定
    app.config["POSTGRES_HOST"] = os.getenv("POSTGRES_HOST", "postgres")
    app.config["POSTGRES_DB"] = os.getenv("POSTGRES_DB", "mydb")
    app.config["POSTGRES_USER"] = os.getenv("POSTGRES_USER", "user")
    app.config["POSTGRES_PASSWORD"] = os.getenv("POSTGRES_PASSWORD", "pass")
    app.config["REDIS_HOST"] = os.getenv("REDIS_HOST", "redis")

    # データベース初期化
    from app.database import init_db
    init_db(app)

    # マイグレーション実行
    with app.app_context():
        perform_migration(app)

    # モデルをインポート（マイグレーションで必要）
    from app import models

    # モデルに定義されたBlueprintを自動登録
    models.register_model_blueprints(app)

    from app import routes
    routes.register_blueprints(app)

    socketio.init_app(app)
    return app

def perform_migration(app):
    """マイグレーションを実行"""
    try:
        # データベース接続テスト
        conn = psycopg2.connect(
            host=app.config["POSTGRES_HOST"],
            database=app.config["POSTGRES_DB"],
            user=app.config["POSTGRES_USER"],
            password=app.config["POSTGRES_PASSWORD"]
        )
        cursor = conn.cursor()
        
        # テーブルの存在確認
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'drivers'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            # テーブルが既に存在する場合はエラー
            logging.error("Driver service: Database tables already exist. Migration aborted.")
            raise Exception("Database tables already exist. Please check if migration is needed.")
        else:
            # テーブルが存在しない場合はマイグレーションディレクトリの確認
            logging.info("Driver service: No existing tables found. Checking migration directory...")
            
            if os.path.exists('migrations/env.py'):
                # マイグレーションファイルが存在する場合はマイグレーション実行
                logging.info("Driver service: Migration files found. Performing migration...")
                from flask_migrate import upgrade
                upgrade()
                logging.info("Driver service: Migration completed successfully.")
            else:
                # マイグレーションファイルが存在しない場合は警告
                logging.warning("Driver service: No migration files found. Tables need to be created manually or migration needs to be initialized.")
                # テーブルを直接作成
                from app.database import db
                db.create_all()
                logging.info("Driver service: Tables created directly using SQLAlchemy.")
            
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        logging.error(f"Driver service: Database connection error: {e}")
        raise
    except Exception as e:
        logging.error(f"Driver service: Migration error: {e}")
        raise
