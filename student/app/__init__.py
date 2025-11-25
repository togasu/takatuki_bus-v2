from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO
import configparser
import logging

def create_app():
    app = Flask(__name__)
    
    # 設定のインポート
    from . import config
    
    # Flask設定
    app.secret_key = config.SECRET_KEY
    app.config['ENV'] = config.FLASK_ENV
    app.config['DEBUG'] = config.FLASK_DEBUG
    
    # 設定ファイルの読み込み（オプション）
    config_ini = configparser.ConfigParser()
    try:
        config_ini.read('setting.ini', encoding='utf-8')
    except Exception as e:
        print(f"設定ファイルの読み込みに失敗しました: {e}")
    
    # Redis設定の初期化
    from .utils.redis_token import RedisTokenManager
    
    # Redisトークンマネージャーの初期化
    try:
        token_manager = RedisTokenManager(
            redis_host=config.REDIS_HOST,
            redis_port=config.REDIS_PORT,
            redis_db=config.REDIS_DB,
            token_expire_minutes=config.SESSION_TIMEOUT_MINUTES
        )
        # グローバルに設定
        app.token_manager = token_manager
    except Exception as e:
        print(f"Redis接続に失敗しました: {e}")
        app.token_manager = None
    
    # データベース設定
    try:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///student.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    except Exception as e:
        print(f"データベース設定に失敗しました: {e}")
        return None
    
    # メール設定
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = 'kutc.shuttlebus@gmail.com'
    app.config['MAIL_PASSWORD'] = 'ecoz ugco asco xnbe'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_DEFAULT_SENDER'] = 'kutc.shuttlebus@gmail.com'
    
    # 拡張機能の初期化
    try:
        from .database import db, migrate
        db.init_app(app)
        migrate.init_app(app, db)
        
        mail = Mail(app)
        
        limiter = Limiter(get_remote_address, app=app, default_limits=["100 per minute"])
        
        # SocketIO初期化
        socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
        app.socketio = socketio
        
        # WebSocketイベントハンドラー登録
        from .routes.ws import register_socketio_events
        register_socketio_events(socketio)
        
    except Exception as e:
        print(f"拡張機能の初期化に失敗しました: {e}")
        return None
    
    # ロガー設定
    logger = logging.getLogger('sojo-bus-log')
    logger.setLevel(10)
    sh = logging.StreamHandler()
    logger.addHandler(sh)
    fh = logging.FileHandler('sojo-bus.log')
    logger.addHandler(fh)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.info('starting student bus server')
    
    # Jinjaフィルターの設定
    try:
        from .utils.datetime_utils import string_to_datetime, datetime_format
        app.jinja_env.filters['string_to_datetime'] = string_to_datetime
        app.jinja_env.filters['datetime_format'] = datetime_format
    except Exception as e:
        print(f"Jinjaフィルターの設定に失敗しました: {e}")
    
    # ブループリントの登録
    try:
        from .routes import register_blueprints
        register_blueprints(app)
    except Exception as e:
        print(f"ブループリントの登録に失敗しました: {e}")
        return None
    
    # エラーハンドラーの登録
    register_error_handlers(app)
    
    # データベースの初期化
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        print(f"データベースの初期化に失敗しました: {e}")
        # データベースエラーでもアプリケーションは起動させる
    
    return app

def register_error_handlers(app):
    """エラーハンドラーの登録"""
    from flask import render_template, request
    
    @app.errorhandler(400)
    def bad_request(error):
        if request.cookies.get('username') is not None:
            username = "jimu"
        elif request.cookies.get('student_id') is not None:
            username = "student"
        else:
            username = None
        return render_template('400.html', username=username), 400

    @app.errorhandler(404)
    def page_not_found(error):
        if request.cookies.get('username') is not None:
            username = "jimu"
        elif request.cookies.get('student_id') is not None:
            username = "student"
        else:
            username = None
        return render_template('404.html', username=username), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        if request.cookies.get('username') is not None:
            username = "jimu"
        elif request.cookies.get('student_id') is not None:
            username = "student"
        else:
            username = None
        return render_template('405.html', username=username), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        if request.cookies.get('username') is not None:
            username = "jimu"
        elif request.cookies.get('student_id') is not None:
            username = "student"
        else:
            username = None
        return render_template('500.html', username=username), 500

    @app.errorhandler(429)
    def ratelimit_error(e):
        return render_template("top.html", message="制限回数を超過しました.10分待ってください")
