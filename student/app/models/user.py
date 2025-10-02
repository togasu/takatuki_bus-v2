from ..database import db
from datetime import datetime, timedelta

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    idm_univ = db.Column(db.String(20), nullable=False)
    idm_bus = db.Column(db.String(20), nullable=False)
    regist_now_time = db.Column(db.DateTime, nullable=False)  # 登録された日時

class User_Penalty(db.Model):
    __tablename__ = "user_penalty"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)  # String型に変更
    end_time_of_usage_restriction = db.Column(db.DateTime, nullable=False)  # 必須フィールドに変更
    reason = db.Column(db.String(200), nullable=False)  # 利用制限の理由
    penalty_type = db.Column(db.String(50), default='manual', nullable=False)  # auto, manual
    applied_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # ペナルティ適用日時
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # ペナルティ有効フラグ

class Penalty_Reservation(db.Model):
    """ペナルティに関連する予約情報"""
    __tablename__ = "penalty_reservation"
    id = db.Column(db.Integer, primary_key=True)
    penalty_id = db.Column(db.Integer, db.ForeignKey('user_penalty.id'), nullable=False)
    reservation_id = db.Column(db.Integer, nullable=False)  # 該当する予約ID
    student_id = db.Column(db.String(20), nullable=False)
    bus_id = db.Column(db.Integer, nullable=False)
    seat_number = db.Column(db.Integer, nullable=False)
    reserved_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class LastSemester_user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    idm_univ = db.Column(db.String(20), nullable=False)
    idm_bus = db.Column(db.String(20), nullable=False)
    regist_now_time = db.Column(db.DateTime, nullable=False)
