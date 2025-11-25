import redis
import json
import hashlib
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import current_app, g
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Redisを使用したセッション管理"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or redis.Redis(
            host='localhost', 
            port=6379, 
            db=0, 
            decode_responses=True
        )
        self.session_prefix = "driver_session:"
        self.session_timeout = 86400  # 24時間（秒）
    
    def create_session(self, username: str) -> str:
        """セッションを作成し、ハッシュキーを返す"""
        try:
            # 既存のセッションを削除
            self.delete_user_session(username)
            
            # 新しいハッシュキーを生成
            session_data = f"{username}{random.randint(0, 1000000)}{datetime.now()}"
            hashed_key = hashlib.sha256(session_data.encode()).hexdigest()
            
            # セッションデータを作成
            session_info = {
                "username": username,
                "login_time": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
            
            # Redisに保存
            session_key = f"{self.session_prefix}{hashed_key}"
            self.redis_client.setex(
                session_key, 
                self.session_timeout, 
                json.dumps(session_info)
            )
            
            # ユーザー名からセッションキーへのマッピングも保存（削除用）
            user_key = f"user_session:{username}"
            self.redis_client.setex(user_key, self.session_timeout, hashed_key)
            
            logger.info(f"Session created for user: {username}")
            return hashed_key
            
        except Exception as e:
            logger.error(f"Failed to create session for {username}: {e}")
            raise
    
    def get_session(self, hashed_key: str) -> Optional[Dict[str, Any]]:
        """セッション情報を取得"""
        try:
            session_key = f"{self.session_prefix}{hashed_key}"
            session_data = self.redis_client.get(session_key)
            
            if not session_data:
                return None
            
            session_info = json.loads(session_data)
            
            # セッションの有効性をチェック
            last_activity = datetime.fromisoformat(session_info["last_activity"])
            if datetime.now() - last_activity > timedelta(seconds=self.session_timeout):
                self.delete_session(hashed_key)
                return None
            
            # 最終アクティビティ時間を更新
            session_info["last_activity"] = datetime.now().isoformat()
            self.redis_client.setex(
                session_key, 
                self.session_timeout, 
                json.dumps(session_info)
            )
            
            return session_info
            
        except Exception as e:
            logger.error(f"Failed to get session {hashed_key}: {e}")
            return None
    
    def delete_session(self, hashed_key: str):
        """セッションを削除"""
        try:
            session_key = f"{self.session_prefix}{hashed_key}"
            
            # セッション情報を取得してユーザー名を確認
            session_data = self.redis_client.get(session_key)
            if session_data:
                session_info = json.loads(session_data)
                username = session_info.get("username")
                if username:
                    user_key = f"user_session:{username}"
                    self.redis_client.delete(user_key)
            
            # セッションを削除
            self.redis_client.delete(session_key)
            logger.info(f"Session deleted: {hashed_key}")
            
        except Exception as e:
            logger.error(f"Failed to delete session {hashed_key}: {e}")
    
    def delete_user_session(self, username: str):
        """ユーザーの既存セッションを削除"""
        try:
            user_key = f"user_session:{username}"
            existing_hash = self.redis_client.get(user_key)
            
            if existing_hash:
                session_key = f"{self.session_prefix}{existing_hash}"
                self.redis_client.delete(session_key)
                self.redis_client.delete(user_key)
                logger.info(f"Existing session deleted for user: {username}")
                
        except Exception as e:
            logger.error(f"Failed to delete user session for {username}: {e}")
    
    def validate_session(self, hashed_key: str) -> Optional[str]:
        """セッションを検証し、ユーザー名を返す"""
        session_info = self.get_session(hashed_key)
        if session_info:
            return session_info.get("username")
        return None
    
    def refresh_session(self, hashed_key: str) -> bool:
        """セッションの有効期限を延長"""
        try:
            session_key = f"{self.session_prefix}{hashed_key}"
            session_data = self.redis_client.get(session_key)
            
            if session_data:
                session_info = json.loads(session_data)
                session_info["last_activity"] = datetime.now().isoformat()
                
                self.redis_client.setex(
                    session_key,
                    self.session_timeout,
                    json.dumps(session_info)
                )
                return True
                
        except Exception as e:
            logger.error(f"Failed to refresh session {hashed_key}: {e}")
        
        return False

# グローバルセッションマネージャーインスタンス
session_manager = SessionManager()

def add_cookie(key: str, value: str):
    """リクエストコンテキストでクッキーを追加"""
    if not hasattr(g, 'cookies'):
        g.cookies = {}
    g.cookies[key] = value