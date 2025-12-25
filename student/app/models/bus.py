from ..database import db

class Bus(db.Model):
    """
    バス便モデル
    
    重要な属性:
    - id: バス便の一意のID（データベース自動生成、例: 1, 2, 3...）
    - busid: バスの号車番号（1～4の固定値、運転手番号と対応）
    
    同じbusid（号車）でも、異なる出発時刻のバス便は別のid（バス便ID）を持ちます。
    例: 1号車が1日に3便運行する場合、busid=1でid=1,10,20のような3つのレコードができます。
    """
    id = db.Column(db.Integer, primary_key=True)
    busid = db.Column(db.Integer, nullable=False) # バスの号車（運転手番号と同じ）１～４までしか割り当てられない
    departure_time = db.Column(db.DateTime, nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    ud = db.Column(db.Integer, nullable=False)  # 上りなら0、下りなら1
    bookable_time = db.Column(db.Integer, nullable=False)  # デフォルト0,予約可能時間に合わせて変更
    status = db.Column(db.Integer, nullable=False) # 0は通常、1はキャンセル待ち（現在機能中止）、2は出発後
