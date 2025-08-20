from app.database import db
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.auth import admin_required
from app.utils.now_jst import now_jst

class Student(db.Model):
    """学生テーブル"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)  # 学籍番号
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255))  # パスワードハッシュ
    password_salt = db.Column(db.String(255))  # パスワードsalt
    created_at = db.Column(db.DateTime, default=now_jst)
    updated_at = db.Column(db.DateTime, default=now_jst, onupdate=now_jst)
    
    def __repr__(self):
        return f'<Student {self.student_id}: {self.name}>'
    
    def set_password(self, password: str):
        """パスワードを設定（簡易版）"""
        # 実際の実装では適切なハッシュ化を行う
        self.password_hash = password
        self.password_salt = "simple_salt"
    
    def check_password(self, password: str) -> bool:
        """パスワード検証（簡易版）"""
        if not self.password_hash:
            # パスワードが設定されていない場合は、任意のパスワードで認証成功（デモ用）
            return bool(password)
        return self.password_hash == password

# Blueprint for Student API
student_bp = Blueprint("student_api", __name__, url_prefix="/api/students")

@student_bp.route("", methods=["GET"])
@admin_required
def get_students():
    """学生一覧を取得"""
    students = Student.query.all()
    return jsonify([{
        "id": s.id,
        "student_id": s.student_id,
        "name": s.name,
        "email": s.email,
        "phone": s.phone,
        "created_at": s.created_at.isoformat() if s.created_at else None
    } for s in students])

@student_bp.route("", methods=["POST"])
@admin_required
def create_student():
    """学生を作成"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ["student_id", "name", "email"]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        student = Student(
            student_id=data["student_id"],
            name=data["name"],
            email=data["email"],
            phone=data.get("phone")
        )
        db.session.add(student)
        db.session.commit()
        
        return jsonify({
            "id": student.id,
            "student_id": student.student_id,
            "name": student.name,
            "message": "Student created successfully"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@student_bp.route("/<int:student_id>", methods=["GET"])
@admin_required
def get_student(student_id):
    """特定の学生を取得"""
    student = Student.query.get_or_404(student_id)
    return jsonify({
        "id": student.id,
        "student_id": student.student_id,
        "name": student.name,
        "email": student.email,
        "phone": student.phone,
        "created_at": student.created_at.isoformat() if student.created_at else None
    })
