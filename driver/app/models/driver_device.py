from app.database import db
from datetime import datetime
from app.utils.now_jst import now_jst

class DriverDevice(db.Model):
    """ドライバー用デバイス管理テーブル - MACアドレスベース認証用"""
    __tablename__ = 'driver_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False, index=True)  # driversテーブルのid
    mac_address = db.Column(db.String(17), nullable=False)  # MACアドレス (XX:XX:XX:XX:XX:XX形式)
    device_name = db.Column(db.String(100))  # デバイス名（識別用）
    is_active = db.Column(db.Boolean, default=True)  # デバイスの有効/無効
    created_at = db.Column(db.DateTime, default=now_jst)
    updated_at = db.Column(db.DateTime, default=now_jst, onupdate=now_jst)
    last_used_at = db.Column(db.DateTime)  # 最終使用日時
    
    # リレーションシップ
    driver = db.relationship('Driver', backref=db.backref('devices', lazy=True))
    
    # 複合ユニーク制約（同じdriver_idに同じMACアドレスは登録できない）
    __table_args__ = (
        db.UniqueConstraint('driver_id', 'mac_address', name='unique_driver_mac'),
    )
    
    def __repr__(self):
        return f'<DriverDevice driver_id={self.driver_id}: {self.mac_address}>'
    
    @staticmethod
    def normalize_mac_address(mac: str) -> str:
        """MACアドレスを正規化 (XX:XX:XX:XX:XX:XX形式)"""
        # ハイフン、コロン、スペースを削除
        mac = mac.replace('-', '').replace(':', '').replace(' ', '').upper()
        
        # 12桁の16進数であることを確認
        if len(mac) != 12:
            raise ValueError(f"Invalid MAC address length: {mac}")
        
        # コロン区切りの形式に変換
        return ':'.join([mac[i:i+2] for i in range(0, 12, 2)])
    
    @classmethod
    def get_devices_by_driver_id(cls, driver_id: int):
        """指定されたdriver_idに紐付くすべてのデバイスを取得"""
        return cls.query.filter_by(driver_id=driver_id, is_active=True).all()
    
    @classmethod
    def get_device_count(cls, driver_id: int) -> int:
        """指定されたdriver_idに紐付く有効なデバイス数を取得"""
        return cls.query.filter_by(driver_id=driver_id, is_active=True).count()
    
    @classmethod
    def is_device_registered(cls, driver_id: int, mac_address: str) -> bool:
        """指定されたdriver_idとMACアドレスの組み合わせが登録されているか確認"""
        try:
            normalized_mac = cls.normalize_mac_address(mac_address)
            device = cls.query.filter_by(
                driver_id=driver_id,
                mac_address=normalized_mac,
                is_active=True
            ).first()
            return device is not None
        except ValueError:
            return False
    
    @classmethod
    def add_device(cls, driver_id: int, mac_address: str, device_name: str = None):
        """新しいデバイスを登録（最大5台まで）"""
        # 現在のデバイス数を確認
        current_count = cls.get_device_count(driver_id)
        if current_count >= 5:
            raise ValueError(f"Maximum device limit (5) reached for driver_id: {driver_id}")
        
        # MACアドレスを正規化
        normalized_mac = cls.normalize_mac_address(mac_address)
        
        # すでに登録されているか確認
        existing = cls.query.filter_by(
            driver_id=driver_id,
            mac_address=normalized_mac
        ).first()
        
        if existing:
            if not existing.is_active:
                # 無効化されていた場合は再有効化
                existing.is_active = True
                existing.updated_at = now_jst()
                if device_name:
                    existing.device_name = device_name
                return existing
            else:
                raise ValueError(f"Device already registered: {normalized_mac}")
        
        # 新しいデバイスを作成
        device = cls(
            driver_id=driver_id,
            mac_address=normalized_mac,
            device_name=device_name or f"Device {current_count + 1}"
        )
        
        db.session.add(device)
        return device
    
    @classmethod
    def remove_device(cls, driver_id: int, mac_address: str):
        """デバイスを削除（無効化）"""
        normalized_mac = cls.normalize_mac_address(mac_address)
        device = cls.query.filter_by(
            driver_id=driver_id,
            mac_address=normalized_mac
        ).first()
        
        if not device:
            raise ValueError(f"Device not found: {normalized_mac}")
        
        device.is_active = False
        device.updated_at = now_jst()
        return device
    
    def update_last_used(self):
        """最終使用日時を更新"""
        self.last_used_at = now_jst()
        self.updated_at = now_jst()
