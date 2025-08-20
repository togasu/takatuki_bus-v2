from app.database import db
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.auth import admin_required
from app.utils.now_jst import now_jst

class Bus(db.Model):
    """バステーブル"""
    __tablename__ = 'buses'
    
    id = db.Column(db.Integer, primary_key=True)
    bus_number = db.Column(db.String(20), unique=True, nullable=False)  # バス番号
    capacity = db.Column(db.Integer, nullable=False)  # 定員
    route = db.Column(db.String(200))  # 路線名
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_jst)
    
    def __repr__(self):
        return f'<Bus {self.bus_number}>'

# Blueprint for Bus API
bus_bp = Blueprint("bus_api", __name__, url_prefix="/api/buses")

@bus_bp.route("", methods=["GET"])
@admin_required
def get_buses():
    """バス一覧を取得"""
    buses = Bus.query.all()
    return jsonify([{
        "id": b.id,
        "bus_number": b.bus_number,
        "capacity": b.capacity,
        "route": b.route,
        "is_active": b.is_active,
        "created_at": b.created_at.isoformat() if b.created_at else None
    } for b in buses])

@bus_bp.route("", methods=["POST"])
@admin_required
def create_bus():
    """バスを作成"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ["bus_number", "capacity"]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        bus = Bus(
            bus_number=data["bus_number"],
            capacity=data["capacity"],
            route=data.get("route"),
            is_active=data.get("is_active", True)
        )
        db.session.add(bus)
        db.session.commit()
        
        return jsonify({
            "id": bus.id,
            "bus_number": bus.bus_number,
            "capacity": bus.capacity,
            "message": "Bus created successfully"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
