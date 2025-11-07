"""ドライバーアプリケーションの初期化とファクトリー関数"""

from flask import Flask, g
from flask_sqlalchemy import SQLAlchemy
import logging
from app.database import db
from app.routes import register_blueprints
from app.models import register_model_blueprints
from app.utils.error_handlers import register_driver_error_handlers
from app.utils.redis_manager import init_redis_manager


def create_driver_app():
    """ドライバーアプリケーションのファクトリー関数"""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # データベース設定
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///driver.db'
    app.config['SQLALCHEMY_BINDS'] = {
        'db2': 'sqlite:///hash.db',  # 互換性のため保持（実際はRedisを使用）
        'db3': 'sqlite:///../../student/instance/yoyaku_seki.db'  # Student serviceのDB
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Redis設定
    app.config['REDIS_HOST'] = 'localhost'
    app.config['REDIS_PORT'] = 6379
    app.config['REDIS_DB'] = 1
    
    # ログ設定
    logger = setup_logging()
    
    # データベース初期化
    db.init_app(app)
    
    # Redis初期化（利用可能な場合のみ）
    try:
        with app.app_context():
            init_redis_manager(app)
        logger.info("Redis session management initialized")
    except ImportError:
        logger.info("Redis not available, using fallback session management")
    except Exception as e:
        logger.warning(f"Redis initialization failed: {e}, using fallback")
    
    # アプリケーションコンテキスト内でテーブル作成
    with app.app_context():
        db.create_all()
    
    # ルーティング登録
    register_blueprints(app)
    
    # モデルのBlueprint登録（必要に応じて）
    register_model_blueprints(app)
    
    # エラーハンドラー登録
    register_driver_error_handlers(app)
    
    # Cookie処理のafter_request
    @app.after_request
    def apply_cookies(response):
        if hasattr(g, 'cookies'):
            for key, value in g.cookies.items():
                response.set_cookie(key, value)
        return response
    
    return app


def setup_logging():
    """ログ設定"""
    logger = logging.getLogger('sojo-bus-log')
    logger.setLevel(10)
    
    # ストリームハンドラー
    sh = logging.StreamHandler()
    logger.addHandler(sh)
    
    # ファイルハンドラー
    fh = logging.FileHandler('sojo-bus.log')
    logger.addHandler(fh)
    
    # フォーマッター
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    fh.setFormatter(formatter)
    
    logger.info('Starting sojo-bus driver server with Redis session management')
    return logger


# 互換性のためのdriver関数
def driver():
    """既存のmain.pyとの互換性を保つためのラッパー関数"""
    return create_driver_app()


if __name__ == '__main__':
    app = create_driver_app()
    app.run(debug=True, port=8080)