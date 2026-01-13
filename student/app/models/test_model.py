from ..database import db

class TestModel(db.Model):
    """動的インポートのテスト用モデル"""
    __tablename__ = "test_model"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<TestModel(id={self.id}, name="{self.name}")>'
    
    def to_dict(self):
        """モデルを辞書形式に変換"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
