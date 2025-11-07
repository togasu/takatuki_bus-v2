from app import create_app, socketio
import os
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # uWSGI用のapplicationオブジェクト
    application = create_app()
    logger.info("Driver service application created successfully")
except Exception as e:
    logger.error(f"Driver service application creation failed: {e}")
    raise

# 開発環境での実行
if __name__ == '__main__':
    # 通常のcreate_appを使用
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=8080)

# uWSGI + gevent で動くため socketio.run は不要
# ただし WebSocket イベントは socketio に登録される
