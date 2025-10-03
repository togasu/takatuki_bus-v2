import redis
import hashlib
import random
import string
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class RedisTokenManager:
    """Redisを使用したトークン管理クラス"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0, token_expire_minutes=15):
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=redis_db, 
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 接続テスト
            self.redis_client.ping()
            print(f"Redis connected successfully to {redis_host}:{redis_port}")
        except redis.ConnectionError as e:
            print(f"Redis connection failed: {e}")
            self.redis_client = None
        except Exception as e:
            print(f"Redis initialization error: {e}")
            self.redis_client = None
            
        self.token_expire_seconds = token_expire_minutes * 60
        
    def generate_token(self) -> str:
        """新しいトークンを生成"""
        token_str = ''.join(random.choice(string.ascii_letters) for i in range(40))
        return hashlib.sha256(token_str.encode()).hexdigest()
    
    def create_session(self, k_number: str, student_id: str) -> Optional[str]:
        """新しいセッションを作成し、既存のセッションを削除"""
        if not self.redis_client:
            print("Redis client not available")
            return None
            
        # 既存のトークンを削除
        self._delete_existing_tokens(k_number, student_id)
        
        # 新しいトークンを生成
        token = self.generate_token()
        
        # セッションデータを作成
        session_data = {
            'k_number': k_number,
            'student_id': student_id,
            'login_time': datetime.now().isoformat()
        }
        
        try:
            # Redisに保存（自動期限切れ設定）
            self.redis_client.setex(
                f"token:{token}",
                self.token_expire_seconds,
                json.dumps(session_data)
            )
            
            # ユーザー別のトークン参照も保存（クリーンアップ用）
            self.redis_client.setex(
                f"user_token:k_number:{k_number}",
                self.token_expire_seconds,
                token
            )
            self.redis_client.setex(
                f"user_token:student_id:{student_id}",
                self.token_expire_seconds,
                token
            )
            
            print(f"Created token: {token}")
            return token
        except Exception as e:
            print(f"Failed to create session: {e}")
            return None

    def create_admin_session(self, username: str, admin_data: Dict[str, Any]) -> Optional[str]:
        """adminユーザー用のセッションを作成"""
        if not self.redis_client:
            print("Redis client not available")
            return None
            
        # 既存のadminトークンを削除
        self._delete_existing_admin_tokens(username)
        
        # 新しいトークンを生成
        token = self.generate_token()
        
        # adminセッションデータを作成
        session_data = {
            'username': username,
            'user_id': admin_data.get('user_id'),
            'role': admin_data.get('role', 'admin'),
            'email': admin_data.get('email'),
            'type': admin_data.get('type', 'admin_user'),
            'login_time': datetime.now().isoformat()
        }
        
        try:
            # Redisに保存（自動期限切れ設定）
            self.redis_client.setex(
                f"admin_token:{token}",
                self.token_expire_seconds,
                json.dumps(session_data)
            )
            
            # adminユーザー別のトークン参照も保存（クリーンアップ用）
            self.redis_client.setex(
                f"admin_user_token:username:{username}",
                self.token_expire_seconds,
                token
            )
            
            print(f"Created admin token: {token}")
            return token
        except Exception as e:
            print(f"Failed to create admin session: {e}")
            return None
    
    def check_session(self, token: str) -> Dict[str, Any]:
        """セッションをチェック（学生用とadmin用の両方に対応）"""
        if not token or not self.redis_client:
            return {'flag': False}
            
        try:
            # まず通常の学生セッションをチェック
            session_data_str = self.redis_client.get(f"token:{token}")
            
            if session_data_str:
                session_data = json.loads(str(session_data_str))
                login_time = datetime.fromisoformat(session_data['login_time'])
                
                # セッションが有効期限内かチェック
                if datetime.now() - login_time < timedelta(minutes=self.token_expire_seconds // 60):
                    return {
                        'flag': True,
                        'k_number': session_data['k_number'],
                        'student_id': session_data['student_id']
                    }
                else:
                    # 期限切れの場合は削除
                    self.delete_session(token)
                    return {'flag': False}
            
            # 次にadminセッションをチェック
            admin_session_data_str = self.redis_client.get(f"admin_token:{token}")
            
            if admin_session_data_str:
                admin_session_data = json.loads(str(admin_session_data_str))
                login_time = datetime.fromisoformat(admin_session_data['login_time'])
                
                # セッションが有効期限内かチェック
                if datetime.now() - login_time < timedelta(minutes=self.token_expire_seconds // 60):
                    return {
                        'flag': True,
                        'username': admin_session_data['username'],
                        'user_id': admin_session_data.get('user_id'),
                        'role': admin_session_data.get('role', 'admin'),
                        'email': admin_session_data.get('email'),
                        'type': admin_session_data.get('type', 'admin_user')
                    }
                else:
                    # 期限切れの場合は削除
                    self.delete_admin_session(token)
                    return {'flag': False}
            
            # どちらにも該当しない場合
            return {'flag': False}
                
        except (json.JSONDecodeError, KeyError, ValueError, Exception) as e:
            print(f"Session check error: {e}")
            # データが破損している場合は削除
            self.delete_session(token)
            self.delete_admin_session(token)
            return {'flag': False}
    
    def delete_session(self, token: str) -> bool:
        """セッションを削除"""
        if not self.redis_client:
            return False
            
        try:
            # セッションデータを取得してから削除
            session_data_str = self.redis_client.get(f"token:{token}")
            if session_data_str:
                session_data = json.loads(str(session_data_str))
                # ユーザー別の参照も削除
                self.redis_client.delete(f"user_token:k_number:{session_data['k_number']}")
                self.redis_client.delete(f"user_token:student_id:{session_data['student_id']}")
            
            # メインのトークンを削除
            return bool(self.redis_client.delete(f"token:{token}"))
        except Exception as e:
            print(f"Failed to delete session: {e}")
            return False

    def delete_admin_session(self, token: str) -> bool:
        """adminセッションを削除"""
        if not self.redis_client:
            return False
            
        try:
            # adminセッションデータを取得してから削除
            admin_session_data_str = self.redis_client.get(f"admin_token:{token}")
            if admin_session_data_str:
                admin_session_data = json.loads(str(admin_session_data_str))
                # adminユーザー別の参照も削除
                self.redis_client.delete(f"admin_user_token:username:{admin_session_data['username']}")
            
            # メインのadminトークンを削除
            return bool(self.redis_client.delete(f"admin_token:{token}"))
        except Exception as e:
            print(f"Failed to delete admin session: {e}")
            return False
    
    def _delete_existing_tokens(self, k_number: str, student_id: str):
        """既存のトークンを削除"""
        if not self.redis_client:
            return
            
        try:
            # k_numberの既存トークンを削除
            existing_token_k = self.redis_client.get(f"user_token:k_number:{k_number}")
            if existing_token_k:
                self.redis_client.delete(f"token:{existing_token_k}")
                self.redis_client.delete(f"user_token:k_number:{k_number}")
            
            # student_idの既存トークンを削除
            existing_token_s = self.redis_client.get(f"user_token:student_id:{student_id}")
            if existing_token_s:
                self.redis_client.delete(f"token:{existing_token_s}")
                self.redis_client.delete(f"user_token:student_id:{student_id}")
        except Exception as e:
            print(f"Failed to delete existing tokens: {e}")

    def _delete_existing_admin_tokens(self, username: str):
        """既存のadminトークンを削除"""
        if not self.redis_client:
            return
            
        try:
            # usernameの既存adminトークンを削除
            existing_token_admin = self.redis_client.get(f"admin_user_token:username:{username}")
            if existing_token_admin:
                self.redis_client.delete(f"admin_token:{existing_token_admin}")
                self.redis_client.delete(f"admin_user_token:username:{username}")
        except Exception as e:
            print(f"Failed to delete existing admin tokens: {e}")

    def refresh_session(self, token: str) -> bool:
        """セッションの有効期限を延長"""
        if not self.redis_client:
            return False
            
        try:
            session_data_str = self.redis_client.get(f"token:{token}")
            if session_data_str:
                # 有効期限を延長
                self.redis_client.expire(f"token:{token}", self.token_expire_seconds)
                
                session_data = json.loads(str(session_data_str))
                self.redis_client.expire(f"user_token:k_number:{session_data['k_number']}", self.token_expire_seconds)
                self.redis_client.expire(f"user_token:student_id:{session_data['student_id']}", self.token_expire_seconds)
                return True
        except Exception as e:
            print(f"Failed to refresh session: {e}")
        
        return False
    
    def get_active_sessions_count(self) -> int:
        """アクティブなセッション数を取得"""
        if not self.redis_client:
            return 0
            
        try:
            keys = self.redis_client.keys("token:*")
            return len(keys)  # type: ignore
        except Exception as e:
            print(f"Failed to get active sessions count: {e}")
            return 0

# 注意: グローバルインスタンスは create_app() で作成されます
