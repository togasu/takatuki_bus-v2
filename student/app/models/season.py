from app.database import db
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.auth import admin_required
from app.utils.now_jst import now_jst

class Season(db.Model):
    """学期テーブル"""
    __tablename__ = 'seasons'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 春学期、秋学期など
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_jst)
    
    def __repr__(self):
        return f'<Season {self.name}>'

# Blueprint for Season API
season_bp = Blueprint("season_api", __name__, url_prefix="/api/seasons")

@season_bp.route("", methods=["GET"])
@admin_required
def get_seasons():
    """学期一覧を取得"""
    seasons = Season.query.all()
    return jsonify([{
        "id": s.id,
        "name": s.name,
        "start_date": s.start_date.isoformat() if s.start_date else None,
        "end_date": s.end_date.isoformat() if s.end_date else None,
        "is_active": s.is_active,
        "created_at": s.created_at.isoformat() if s.created_at else None
    } for s in seasons])

@season_bp.route("", methods=["POST"])
@admin_required
def create_season():
    """学期を作成"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ["name", "start_date", "end_date"]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        from datetime import datetime
        season = Season(
            name=data["name"],
            start_date=datetime.strptime(data["start_date"], "%Y-%m-%d").date(),
            end_date=datetime.strptime(data["end_date"], "%Y-%m-%d").date(),
            is_active=data.get("is_active", False)
        )
        db.session.add(season)
        db.session.commit()
        
        return jsonify({
            "id": season.id,
            "name": season.name,
            "message": "Season created successfully"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
