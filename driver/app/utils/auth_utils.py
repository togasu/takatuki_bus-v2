import bcrypt
import secrets
import redis
import json
import os
from datetime import datetime, timedelta

class PasswordManager:
    """パスワードハッシュ化とsalt管理"""
    
    @staticmethod
    def hash_password(password: str) -> tuple:
        """
        パスワードをハッシュ化
        Returns: (salt, password_hash)
        """
        # salt生成
        salt = bcrypt.gensalt()
        # パスワードハッシュ化
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        return salt.decode('utf-8'), password_hash.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, salt: str, stored_hash: str) -> bool:
        """
        パスワード検証
        """
        try:
            salt_bytes = salt.encode('utf-8')
            stored_hash_bytes = stored_hash.encode('utf-8')
            
            # 入力されたパスワードをハッシュ化
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt_bytes)
            
            # ハッシュ比較
            return password_hash.decode('utf-8') == stored_hash
        except Exception:
            return False

class SessionManager:
    """Redisベースのセッション管理"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_SESSION_DB', 2)),  # ドライバー用のDB
            decode_responses=True
        )
        self.session_timeout = int(os.getenv('SESSION_TIMEOUT', 3600))  # 1時間
    
    def create_session(self, driver_id: str, driver_data: dict) -> str:
        """
        セッション作成
        Returns: session_token
        """
        # セッショントークン生成
        session_token = secrets.token_hex(32)
        
        # セッションデータ
        session_data = {
            'driver_id': driver_id,
            'driver_data': driver_data,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()
        }
        
        # Redisに保存
        session_key = f"driver_session:{session_token}"
        self.redis_client.setex(
            session_key,
            self.session_timeout,
            json.dumps(session_data)
        )
        
        return session_token
    
    def get_session(self, session_token: str) -> dict:
        """
        セッション取得
        """
        if not session_token:
            return None
        
        session_key = f"driver_session:{session_token}"
        session_data_str = self.redis_client.get(session_key)
        
        if not session_data_str:
            return None
        
        try:
            session_data = json.loads(session_data_str)
            
            # 有効期限チェック
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.now() > expires_at:
                self.delete_session(session_token)
                return None
            
            return session_data
        except Exception:
            return None
    
    def delete_session(self, session_token: str) -> bool:
        """
        セッション削除
        """
        if not session_token:
            return False
        
        session_key = f"driver_session:{session_token}"
        return bool(self.redis_client.delete(session_key))
    
    def validate_session(self, session_token: str) -> dict:
        """
        セッション検証（有効期限も自動更新）
        """
        session_data = self.get_session(session_token)
        if session_data:
            # 有効期限を更新
            session_data['expires_at'] = (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()
            session_key = f"driver_session:{session_token}"
            self.redis_client.setex(
                session_key,
                self.session_timeout,
                json.dumps(session_data)
            )
        return session_data
