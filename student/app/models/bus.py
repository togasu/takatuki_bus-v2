from ..database import db

class Bus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    busid = db.Column(db.Integer, nullable=False)
    departure_time = db.Column(db.DateTime, nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    ud = db.Column(db.Integer, nullable=False)  # 上りなら0、下りなら1
    bookable_time = db.Column(db.Integer, nullable=False)  # デフォルト0,予約可能時間に合わせて変更
    status = db.Column(db.Integer, nullable=False)
