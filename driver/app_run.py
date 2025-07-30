from app import create_app, socketio

# Flaskアプリ作成
app = create_app()

# uWSGI + gevent で動くため socketio.run は不要
# ただし WebSocket イベントは socketio に登録される
