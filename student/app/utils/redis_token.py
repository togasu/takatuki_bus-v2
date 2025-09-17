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
    
    def check_session(self, token: str) -> Dict[str, Any]:
        """セッションをチェック"""
        if not token or not self.redis_client:
            return {'flag': False}
            
        try:
            # Redisからセッションデータを取得
            session_data_str = self.redis_client.get(f"token:{token}")
            
            if not session_data_str:
                return {'flag': False}
            
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
                
        except (json.JSONDecodeError, KeyError, ValueError, Exception) as e:
            print(f"Session check error: {e}")
            # データが破損している場合は削除
            self.delete_session(token)
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
            return len(list(keys))
        except Exception as e:
            print(f"Failed to get active sessions count: {e}")
            return 0

# 注意: グローバルインスタンスは create_app() で作成されます
