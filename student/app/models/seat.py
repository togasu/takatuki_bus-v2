from ..database import db

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    bus_id = db.Column(db.Integer, nullable=False)  # Bus.idを入れている
    reservations = db.relationship('Reservation', backref='seat', lazy=True)
