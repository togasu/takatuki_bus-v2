import sys
import traceback
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    logger.info("Starting driver service application...")
    
    # モジュールのインポート
    logger.info("Importing app modules...")
    from app import create_app, socketio
    logger.info("App modules imported successfully")
    
    # Flaskアプリ作成
    logger.info("Creating Flask application...")
    app = create_app()
    logger.info("Flask application created successfully")
    
    # uWSGI + gevent で動くため socketio.run は不要
    # ただし WebSocket イベントは socketio に登録される
    
    # アプリケーションが正常に作成されたことをログに記録
    logger.info(f"Driver service app is ready. App type: {type(app)}")
    
except Exception as e:
    logger.error(f"Failed to create driver service application: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)
