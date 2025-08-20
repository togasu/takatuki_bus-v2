from app.database import db
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.auth import admin_required
from app.utils.now_jst import now_jst

class Course(db.Model):
    """コーステーブル"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)  # 科目コード
    course_name = db.Column(db.String(100), nullable=False)  # 科目名
    instructor = db.Column(db.String(100))  # 担当教員
    credits = db.Column(db.Integer, default=2)  # 単位数
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_jst)
    
    def __repr__(self):
        return f'<Course {self.course_code}: {self.course_name}>'

# Blueprint for Course API
course_bp = Blueprint("course_api", __name__, url_prefix="/api/courses")

@course_bp.route("", methods=["GET"])
@admin_required
def get_courses():
    """コース一覧を取得"""
    courses = Course.query.all()
    return jsonify([{
        "id": c.id,
        "course_code": c.course_code,
        "course_name": c.course_name,
        "instructor": c.instructor,
        "credits": c.credits,
        "is_active": c.is_active,
        "created_at": c.created_at.isoformat() if c.created_at else None
    } for c in courses])

@course_bp.route("", methods=["POST"])
@admin_required
def create_course():
    """コースを作成"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ["course_code", "course_name"]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        course = Course(
            course_code=data["course_code"],
            course_name=data["course_name"],
            instructor=data.get("instructor"),
            credits=data.get("credits", 2),
            is_active=data.get("is_active", True)
        )
        db.session.add(course)
        db.session.commit()
        
        return jsonify({
            "id": course.id,
            "course_code": course.course_code,
            "course_name": course.course_name,
            "message": "Course created successfully"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
