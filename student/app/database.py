from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import current_app
import psycopg2

# データベースインスタンス
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """データベースの初期化"""
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql://{app.config['POSTGRES_USER']}:"
        f"{app.config['POSTGRES_PASSWORD']}@"
        f"{app.config['POSTGRES_HOST']}/"
        f"{app.config['POSTGRES_DB']}?client_encoding=utf8"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    return db

def get_db_connection():
    """PostgreSQLへの直接接続を取得"""
    return psycopg2.connect(
        host=current_app.config["POSTGRES_HOST"],
        database=current_app.config["POSTGRES_DB"],
        user=current_app.config["POSTGRES_USER"],
        password=current_app.config["POSTGRES_PASSWORD"],
        options='-c client_encoding=utf8'
    )
