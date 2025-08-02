from flask import Flask, request
from flask_socketio import SocketIO
import os
import logging

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

    from app import routes
    routes.register_blueprints(app)

    socketio.init_app(app)
    return app
