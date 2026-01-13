"""ドライバーから管理者へのメッセージモデル"""

from app.database import db
from datetime import datetime


class DriverMessage(db.Model):
    """ドライバーから管理者へのメッセージ"""
    __tablename__ = 'driver_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    driver_username = db.Column(db.String(100), nullable=False)  # driver1, driver2など
    subject = db.Column(db.String(200), nullable=False)  # 件名
    message = db.Column(db.Text, nullable=False)  # メッセージ本文
    priority = db.Column(db.String(20), default='normal')  # normal, urgent
    is_read = db.Column(db.Boolean, default=False)  # 既読フラグ
    read_at = db.Column(db.DateTime, nullable=True)  # 既読日時
    replied = db.Column(db.Boolean, default=False)  # 返信済みフラグ
    reply_message = db.Column(db.Text, nullable=True)  # 返信メッセージ
    replied_at = db.Column(db.DateTime, nullable=True)  # 返信日時
    replied_by = db.Column(db.String(100), nullable=True)  # 返信者
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 作成日時
    
    # リレーション
    driver = db.relationship('Driver', backref=db.backref('messages', lazy='dynamic'))
    
    def __repr__(self):
        return f'<DriverMessage {self.id}: {self.subject} from {self.driver_username}>'
    
    def mark_as_read(self, admin_username=None):
        """既読にする"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()
    
    def add_reply(self, reply_text, admin_username):
        """返信を追加"""
        self.replied = True
        self.reply_message = reply_text
        self.replied_at = datetime.utcnow()
        self.replied_by = admin_username
        db.session.commit()
    
    def to_dict(self):
        """辞書形式に変換"""
        return {
            'id': self.id,
            'driver_id': self.driver_id,
            'driver_username': self.driver_username,
            'subject': self.subject,
            'message': self.message,
            'priority': self.priority,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'replied': self.replied,
            'reply_message': self.reply_message,
            'replied_at': self.replied_at.isoformat() if self.replied_at else None,
            'replied_by': self.replied_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
