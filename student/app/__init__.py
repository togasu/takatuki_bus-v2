from flask import Flask
from flask_socketio import SocketIO
import os

socketio = SocketIO(cors_allowed_origins="*", async_mode="gevent")

def create_app():
    app = Flask(__name__)

    # DB設定
    app.config["POSTGRES_HOST"] = os.getenv("POSTGRES_HOST", "postgres")
    app.config["POSTGRES_DB"] = os.getenv("POSTGRES_DB", "mydb")
    app.config["POSTGRES_USER"] = os.getenv("POSTGRES_USER", "user")
    app.config["POSTGRES_PASSWORD"] = os.getenv("POSTGRES_PASSWORD", "pass")
    app.config["REDIS_HOST"] = os.getenv("REDIS_HOST", "redis")

    from app import routes
    routes.register_blueprints(app)

    socketio.init_app(app)
    return app
