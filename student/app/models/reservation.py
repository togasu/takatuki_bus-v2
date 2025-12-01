from ..database import db

class Reservation(db.Model):
    __tablename__ = 'Reservation'  # テーブル名を指定
    id = db.Column(db.Integer, primary_key=True)
    seat_number = db.Column(db.Integer, nullable=False)  # 外部キー制約を削除（numberは主キーではないため）
    bus_id = db.Column(db.Integer, db.ForeignKey('bus.id'), nullable=False)
    user_id = db.Column(db.String(50), nullable=False)  # admin/driver対応のため文字列型に変更
    approved = db.Column(db.Integer, nullable=False)  # 0なら未認証(デフォルト)、1なら認証済み
    reserved_time = db.Column(db.DateTime)
