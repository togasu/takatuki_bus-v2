from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# データベースインスタンス
db = SQLAlchemy()
migrate = Migrate()

# データベース設定
DATABASE_CONFIG = {
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///student.db',  # 適切なURIに変更してください
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
}
