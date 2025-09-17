from ..database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    idm_univ = db.Column(db.String(20), nullable=False)
    idm_bus = db.Column(db.String(20), nullable=False)
    regist_now_time = db.Column(db.DateTime, nullable=False)  # 登録された日時

class User_Penalty(db.Model):
    __tablename__ = "user_penalty"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    penalty_count = db.Column(db.Integer)
    penalty_time = db.Column(db.DateTime)

class LastSemester_user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    idm_univ = db.Column(db.String(20), nullable=False)
    idm_bus = db.Column(db.String(20), nullable=False)
    regist_now_time = db.Column(db.DateTime, nullable=False)
