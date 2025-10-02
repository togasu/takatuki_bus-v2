from app import create_app, socketio

# Flaskアプリ作成
app = create_app()

# スタンドアローン版を作成する場合は以下を使用
# from app import create_standalone_app
# app = create_standalone_app()

# 開発環境での実行
if __name__ == '__main__':
    # 開発時はスタンドアローン版を使用
    from app import create_standalone_app
    app = create_standalone_app()
    app.run(debug=True, port=8080)

# uWSGI + gevent で動くため socketio.run は不要
# ただし WebSocket イベントは socketio に登録される
