from app.database import db
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.auth import admin_required
from app.utils.now_jst import now_jst

class Seat(db.Model):
    """座席テーブル"""
    __tablename__ = 'seats'
    
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    season_id = db.Column(db.Integer, db.ForeignKey('seasons.id'), nullable=False)
    seat_number = db.Column(db.String(10), nullable=False)  # 座席番号（例：1A, 2B）
    reservation_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='available')  # available, reserved, occupied
    created_at = db.Column(db.DateTime, default=now_jst)
    updated_at = db.Column(db.DateTime, default=now_jst, onupdate=now_jst)
    
    # リレーション
    bus = db.relationship('Bus', backref=db.backref('seats', lazy=True))
    student = db.relationship('Student', backref=db.backref('seats', lazy=True))
    season = db.relationship('Season', backref=db.backref('seats', lazy=True))
    
    def __repr__(self):
        return f'<Seat {self.seat_number} in Bus {self.bus_id}>'

# Blueprint for Seat API
seat_bp = Blueprint("seat_api", __name__, url_prefix="/api/seats")

@seat_bp.route("", methods=["GET"])
@admin_required
def get_seats():
    """座席一覧を取得"""
    seats = Seat.query.all()
    return jsonify([{
        "id": s.id,
        "bus_id": s.bus_id,
        "student_id": s.student_id,
        "season_id": s.season_id,
        "seat_number": s.seat_number,
        "status": s.status,
        "reservation_date": s.reservation_date.isoformat() if s.reservation_date else None,
        "created_at": s.created_at.isoformat() if s.created_at else None
    } for s in seats])

@seat_bp.route("", methods=["POST"])
@admin_required
def create_seat():
    """座席を作成"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ["bus_id", "season_id", "seat_number"]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        seat = Seat(
            bus_id=data["bus_id"],
            season_id=data["season_id"],
            seat_number=data["seat_number"],
            student_id=data.get("student_id"),
            status=data.get("status", "available")
        )
        db.session.add(seat)
        db.session.commit()
        
        return jsonify({
            "id": seat.id,
            "seat_number": seat.seat_number,
            "bus_id": seat.bus_id,
            "message": "Seat created successfully"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
