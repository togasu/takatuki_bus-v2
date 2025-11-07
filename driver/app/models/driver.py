from app.database import db
from datetime import datetime
from app.utils.now_jst import now_jst
from app.utils.auth_utils import PasswordManager
import hashlib

class Driver(db.Model):
    """ドライバーテーブル - ドライバーサービス固有のテーブル"""
    __tablename__ = 'drivers'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)  # ユーザー名
    number = db.Column(db.Integer, unique=True, nullable=False)  # 運転手番号
    password = db.Column(db.String, unique=False, nullable=False)  # パスワード(暗号化)
    salt = db.Column(db.String, unique=False, nullable=False)  # パスワードの暗号化に使用するsalt
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_jst)
    updated_at = db.Column(db.DateTime, default=now_jst, onupdate=now_jst)
    
    def __repr__(self):
        return f'<Driver {self.username}: {self.number}>'
    
    def set_password(self, password: str):
        """パスワードを設定（ハッシュ化とsalt生成）"""
        if password:
            salt, password_hash = PasswordManager.hash_password(password)
            self.salt = salt
            self.password = password_hash
    
    def verify_password(self, password: str) -> bool:
        """パスワード検証"""
        if not self.password or not self.salt:
            return False
        
        stored_password = self.password
        stored_salt = self.salt
        
        library_hashed = hashlib.pbkdf2_hmac(
            'sha256', password.encode('utf-8'), stored_salt, 1000
        )
        return library_hashed == stored_password

class QA(db.Model):
    """Q&Aを格納するテーブル"""
    __tablename__ = 'qa'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), unique=False, nullable=False)  # 質問
    answer = db.Column(db.String(255), unique=False, nullable=False)  # 回答
    createuser = db.Column(db.String(80), unique=False, nullable=False)  # 作成者
    createdate = db.Column(db.DateTime, nullable=False, default=now_jst)  # 作成日時

# Hashテーブルは削除（Redis使用）

# バスの情報を格納するテーブル
class Bus(db.Model):
    __bind_key__ = "db3"
    id = db.Column(db.Integer, primary_key=True)
    busid = db.Column(db.Integer, nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    ud = db.Column(db.Integer, nullable=False)  # 上りなら0、下りなら1
    bookable_time = db.Column(db.Integer, nullable=False)  # デフォルト0,予約可能時間に合わせて変更
    status = db.Column(db.Integer, nullable=False)

class Seat(db.Model):
    __bind_key__ = "db3"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    bus_id = db.Column(db.Integer, nullable=False) # Bus.idを入れている
    reservations = db.relationship('Reservation', backref='seat', lazy=True)

class Reservation(db.Model):
    __bind_key__ = "db3"
    __tablename__ = 'Reservation' #テーブル名を指定
    id = db.Column(db.Integer, primary_key=True)
    seat_number = db.Column(db.Integer, db.ForeignKey('seat.number'), nullable=False)
    bus_id = db.Column(db.Integer, db.ForeignKey('bus.id'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    approved = db.Column(db.Integer, nullable=False) # 0なら未認証(デフォルト)、1なら認証済み
    reserved_time = db.Column(db.DateTime)


