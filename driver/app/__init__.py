from flask import Flask, request
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import logging

socketio = SocketIO(cors_allowed_origins="*", async_mode="gevent")

def create_app():
    """ドライバーサービスのFlaskアプリケーションを作成"""
    app = Flask(__name__)
    
    # Nginxリバースプロキシ環境用設定
    app.config['APPLICATION_ROOT'] = '/driver'
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

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

    @app.context_processor
    def inject_url_vars():
        """テンプレートで使用するURL変数を注入"""
        return dict(base_url='/driver')

    # DB設定（Docker環境ではPostgreSQLを使用）
    app.config["USE_SQLITE"] = os.getenv('USE_SQLITE', 'false').lower() == 'true'
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
        # データベースが正しく初期化されているかチェック
        from app.database import db
        if db is None:
            logging.error("Driver service: Database not initialized")
            return
            
        # マイグレーション関連のライブラリをチェック
        try:
            from flask_migrate import Migrate, upgrade, init, migrate as flask_migrate
            
            migrate = Migrate()
            migrate.init_app(app, db)
            
            # マイグレーションディレクトリが存在するかチェック
            if os.path.exists('migrations'):
                try:
                    upgrade()
                    logging.info("Driver service: Migration completed successfully")
                except Exception as e:
                    logging.warning(f"Driver service: Migration failed, creating tables directly: {e}")
                    with app.app_context():
                        db.create_all()
                        logging.info("Driver service: Tables created directly")
            else:
                logging.info("Driver service: No migration directory found, creating tables directly")
                with app.app_context():
                    db.create_all()
                    logging.info("Driver service: Tables created directly")
                    
        except ImportError:
            logging.info("Driver service: Flask-Migrate not available, creating tables directly")
            with app.app_context():
                db.create_all()
                logging.info("Driver service: Tables created directly")
                
    except Exception as e:
        logging.error(f"Driver service: Migration error: {e}")
        # フォールバック：直接テーブル作成
        try:
            from app.database import db
            if db is not None:
                with app.app_context():
                    db.create_all()
                    logging.info("Driver service: Fallback table creation completed")
        except Exception as fallback_error:
            logging.error(f"Driver service: Fallback table creation failed: {fallback_error}")

def create_standalone_app():
    """スタンドアローン版のアプリケーション（index.pyを直接使用）"""
    from app.index import create_app
    return create_app()
