import bcrypt
import secrets
import redis
import json
import os
import requests
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

class DeviceAuthManager:
    """MACアドレスベースのデバイス認証マネージャー"""
    
    def __init__(self):
        # 管理システムのURL（環境変数から取得）
        self.admin_api_url = os.getenv('ADMIN_API_URL', 'http://admin:5000')
        
    @staticmethod
    def get_client_mac_address(request) -> str:
        """
        クライアントのMACアドレスを取得
        
        注意: 通常のHTTPリクエストではMACアドレスを直接取得できないため、
        以下のいずれかの方法で取得する必要があります:
        1. リバースプロキシ(nginx等)でカスタムヘッダーに設定
        2. クライアント側JavaScriptで取得してヘッダーに含める（セキュリティリスクあり）
        3. VPN等で管理されたネットワーク内でARPテーブルから取得
        
        この実装では、カスタムヘッダー 'X-Client-MAC' から取得することを想定
        """
        # カスタムヘッダーからMACアドレスを取得
        mac_address = request.headers.get('X-Client-MAC')
        
        if not mac_address:
            # フォールバック: X-Forwarded-For等からIPを取得し、
            # サーバー側でARPテーブルを参照する方法も考えられるが、
            # セキュリティ上の理由から推奨されない
            return None
        
        return mac_address
    
    def verify_device_with_admin(self, username: str, mac_address: str) -> bool:
        """
        管理システムのAPIを呼び出してデバイスが登録されているか確認
        
        Args:
            username: ドライバーのユーザー名
            mac_address: 検証するMACアドレス
            
        Returns:
            bool: デバイスが登録されている場合True
        """
        try:
            # 管理システムのAPIエンドポイント
            verify_url = f"{self.admin_api_url}/api/driver-devices/{username}/verify"
            
            # APIリクエスト
            response = requests.post(
                verify_url,
                json={"mac_address": mac_address},
                timeout=5,
                verify=False  # 開発環境用（本番ではverify=Trueにすること）
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('is_registered', False)
            else:
                # APIエラーの場合は認証失敗として扱う
                return False
                
        except Exception as e:
            # ネットワークエラー等の場合は認証失敗として扱う
            print(f"Error verifying device with admin API: {e}")
            return False
    
    def authenticate_by_device(self, request, username: str) -> bool:
        """
        デバイス（MACアドレス）による認証
        
        Args:
            request: Flaskのrequestオブジェクト
            username: 認証するドライバーのユーザー名
            
        Returns:
            bool: 認証成功の場合True
        """
        # MACアドレスを取得
        mac_address = self.get_client_mac_address(request)
        
        if not mac_address:
            return False
        
        # 管理システムに問い合わせて認証
        return self.verify_device_with_admin(username, mac_address)

