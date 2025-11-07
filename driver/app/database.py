from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """データベースの初期化"""
    # Docker環境ではPostgreSQLを使用、ローカル開発環境ではSQLiteを使用
    if app.config.get('USE_SQLITE', False):
        import os
        db_path = os.path.join(os.getcwd(), 'driver.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        print(f"Using SQLite database at: {db_path}")
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"postgresql://{app.config['POSTGRES_USER']}:"
            f"{app.config['POSTGRES_PASSWORD']}@"
            f"{app.config['POSTGRES_HOST']}/"
            f"{app.config['POSTGRES_DB']}"
        )
        print(f"Using PostgreSQL database at: {app.config['POSTGRES_HOST']}")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    return db
