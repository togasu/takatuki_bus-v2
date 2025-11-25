from ..database import db

class Cancel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), nullable=False)
    bus_id = db.Column(db.Integer, nullable=False)
    seat_number = db.Column(db.Integer)
    cancel_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)
