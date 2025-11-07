from ..database import db
from datetime import datetime

class Semester(db.Model):
    """学期管理テーブル"""
    __tablename__ = "semester"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # 学期名（例：「2024年秋学期」）
    start_date = db.Column(db.Date, nullable=False)  # 学期開始日
    end_date = db.Column(db.Date, nullable=False)    # 学期終了日
    is_active = db.Column(db.Boolean, default=False, nullable=False)  # アクティブな学期かどうか
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Semester {self.name}: {self.start_date} - {self.end_date}>'
    
    def is_current_semester(self):
        """現在の日付が学期期間内かどうかをチェック"""
        today = datetime.now().date()
        return self.start_date <= today <= self.end_date
    
    def to_dict(self):
        """辞書形式に変換"""
        return {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class SemesterTransition(db.Model):
    """学期切り替え履歴テーブル"""
    __tablename__ = "semester_transition"
    
    id = db.Column(db.Integer, primary_key=True)
    from_semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=True)  # 切り替え前学期
    to_semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)   # 切り替え後学期
    transition_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)      # 切り替え実行日時
    users_migrated = db.Column(db.Integer, default=0, nullable=False)                      # 移行されたユーザー数
    status = db.Column(db.String(20), default='completed', nullable=False)                 # completed, failed
    notes = db.Column(db.Text)  # 切り替え時のメモ
    
    # リレーション
    from_semester = db.relationship('Semester', foreign_keys=[from_semester_id], backref='transitions_from')
    to_semester = db.relationship('Semester', foreign_keys=[to_semester_id], backref='transitions_to')
    
    def __repr__(self):
        return f'<SemesterTransition {self.from_semester_id} -> {self.to_semester_id}>'