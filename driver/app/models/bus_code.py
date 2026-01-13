"""バス運行便コード管理モデル"""
from app.database import db
from datetime import datetime, timedelta
from app.utils.now_jst import now_jst
import random
import string

class BusCode(db.Model):
    """バス運行便コード管理テーブル
    
    運転手がバスの運行便を設定したときに6桁のコードを生成し、
    auth_systemがそのコードを使ってバス情報を取得できるようにする。
    """
    __tablename__ = 'bus_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(6), unique=True, nullable=False, index=True)  # 6桁の数字コード
    bus_id = db.Column(db.Integer, nullable=False)  # Bus.id (バス便ID)
    busid = db.Column(db.Integer, nullable=False)  # バスの号車番号（1-4）
    departure_time = db.Column(db.DateTime, nullable=False)  # 出発時刻
    ud = db.Column(db.Integer, nullable=False)  # 上り(0)/下り(1)
    created_at = db.Column(db.DateTime, default=now_jst, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)  # コードの有効期限
    is_used = db.Column(db.Boolean, default=False, nullable=False)  # 使用済みフラグ
    used_at = db.Column(db.DateTime, nullable=True)  # 使用日時
    
    def __repr__(self):
        return f'<BusCode {self.code}: Bus{self.busid} at {self.departure_time}>'
    
    @staticmethod
    def generate_code():
        """6桁のランダムな数字コードを生成"""
        return ''.join(random.choices(string.digits, k=6))
    
    @classmethod
    def create_code(cls, bus_id: int, busid: int, departure_time: datetime, ud: int, expires_hours: int = 24):
        """新しいバスコードを生成して保存
        
        Args:
            bus_id: バス便ID
            busid: バスの号車番号
            departure_time: 出発時刻
            ud: 上り(0)/下り(1)
            expires_hours: コードの有効期限（時間）
        
        Returns:
            BusCode: 作成されたバスコードオブジェクト
        """
        # 既存の未使用コードがあればそれを返す
        existing = cls.query.filter_by(
            bus_id=bus_id,
            is_used=False
        ).filter(cls.expires_at > now_jst()).first()
        
        if existing:
            return existing
        
        # ユニークなコードを生成（最大10回試行）
        for _ in range(10):
            code = cls.generate_code()
            if not cls.query.filter_by(code=code).first():
                break
        else:
            raise ValueError("Failed to generate unique code")
        
        bus_code = cls(
            code=code,
            bus_id=bus_id,
            busid=busid,
            departure_time=departure_time,
            ud=ud,
            expires_at=now_jst() + timedelta(hours=expires_hours)
        )
        
        db.session.add(bus_code)
        db.session.commit()
        
        return bus_code
    
    @classmethod
    def verify_code(cls, code: str):
        """コードを検証して対応するバス情報を取得
        
        Args:
            code: 6桁のコード
        
        Returns:
            tuple: (成功フラグ, メッセージ, BusCodeオブジェクトまたはNone)
        """
        if not code or len(code) != 6 or not code.isdigit():
            return False, "無効なコード形式です", None
        
        bus_code = cls.query.filter_by(code=code).first()
        
        if not bus_code:
            return False, "コードが見つかりません", None
        
        if bus_code.is_used:
            return False, "このコードは既に使用済みです", None
        
        if bus_code.expires_at < now_jst():
            return False, "このコードは期限切れです", None
        
        return True, "コード検証成功", bus_code
    
    def mark_as_used(self):
        """コードを使用済みとしてマーク"""
        self.is_used = True
        self.used_at = now_jst()
        db.session.commit()
