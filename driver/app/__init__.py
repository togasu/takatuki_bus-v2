from flask import Flask, request
from flask_socketio import SocketIO
import os
import logging

socketio = SocketIO(cors_allowed_origins="*", async_mode="gevent")

def create_app():
    """ドライバーサービスのFlaskアプリケーションを作成"""
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

    # DB設定（MIGRATION_GUIDEに従った設定）
    app.config["POSTGRES_HOST"] = os.getenv("POSTGRES_HOST", "postgres")
    app.config["POSTGRES_DB"] = os.getenv("POSTGRES_DB", "mydb")
    app.config["POSTGRES_USER"] = os.getenv("POSTGRES_USER", "user")
    app.config["POSTGRES_PASSWORD"] = os.getenv("POSTGRES_PASSWORD", "pass")
    app.config["REDIS_HOST"] = os.getenv("REDIS_HOST", "redis")

    # データベース初期化
    from app.database import init_db
    init_db(app)

    # マイグレーション実行（MIGRATION_GUIDEに従って）
    if not os.getenv('SKIP_MIGRATION', '').lower() == 'true':
        with app.app_context():
            perform_migration(app)

    # モデルのインポート（マイグレーション後）
    from app import models
    
    # モデルに定義されたBlueprintを自動登録
    models.register_model_blueprints(app)

    # APIルート
    from app import routes
    routes.register_blueprints(app)

    # WebSocket初期化
    socketio.init_app(app)

    # エラーハンドラーを登録
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    return app

def perform_migration(app):
    """マイグレーション実行（簡易版）"""
    try:
        # マイグレーション関連のライブラリをチェック
        try:
            from flask_migrate import Migrate, upgrade, init, migrate as flask_migrate
            
            migrate = Migrate()
            migrate.init_app(app)
            
            # マイグレーションディレクトリが存在するかチェック
            if os.path.exists('migrations'):
                try:
                    upgrade()
                    logging.info("Driver service: Migration completed successfully")
                except Exception as e:
                    logging.warning(f"Driver service: Migration failed, creating tables directly: {e}")
                    from app.database import db
                    with app.app_context():
                        db.create_all()
            else:
                logging.info("Driver service: No migration directory found, creating tables directly")
                from app.database import db
                with app.app_context():
                    db.create_all()
                    
        except ImportError:
            logging.info("Driver service: Flask-Migrate not available, creating tables directly")
            from app.database import db
            with app.app_context():
                db.create_all()
                
    except Exception as e:
        logging.error(f"Driver service: Migration error: {e}")
        # フォールバック：直接テーブル作成
        from app.database import db
        with app.app_context():
            db.create_all()

def create_standalone_app():
    """スタンドアローン版のアプリケーション（index.pyを直接使用）"""
    from app.index import create_app
    return create_app()
