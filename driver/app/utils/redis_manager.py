"""Redis管理クラス（開発環境ではダミー実装）"""

import json
import hashlib
import random
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger('sojo-bus-log')


class RedisManager:
    """Redisによるハッシュとセッション管理（開発環境ではダミー実装）"""
    
    def __init__(self, host='localhost', port=6379, db=1, decode_responses=True):
        """Redis接続を初期化（開発環境では無効化）"""
        self.redis_client = None
        logger.info("Redis disabled in development mode - using fallback")
    
    def generate_hash_login(self, username: str) -> Optional[str]:
        """ログイン時にハッシュ化された番号を生成（ダミー実装）"""
        try:
            # ダミーハッシュを生成
            hash_string = username + str(random.randint(0, 1000000)) + str(datetime.now())
            hashed_num = hashlib.sha256(hash_string.encode()).hexdigest()[:12]
            
            logger.info(f"Generated dummy hash for user {username}: {hashed_num}")
            return hashed_num
        except Exception as e:
            logger.error(f"Error generating hash: {e}")
            return None
            hashed_num = hashlib.sha256(hash_string.encode()).hexdigest()
            
            # Redis に保存（24時間有効）
            hash_data = {
                'username': username,
                'last_login': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            # ハッシュキーとユーザー名の両方向でマッピング
            self.redis_client.setex(f"hash:{hashed_num}", 86400, json.dumps(hash_data))  # 24時間
            self.redis_client.setex(f"user:{username}", 86400, hashed_num)  # 24時間
            
            logger.info(f"Hash generated for user: {username}")
            return hashed_num
            
        except Exception as e:
            logger.error(f"Failed to generate hash for {username}: {e}")
            return None
    
    def check_hash(self, hashed_num: str) -> Optional[str]:
        """ハッシュを検証してユーザー名を返す"""
        try:
            hash_data_str = self.redis_client.get(f"hash:{hashed_num}")
            if not hash_data_str:
                return None
            
            hash_data = json.loads(hash_data_str)
            username = hash_data['username']
            last_login = datetime.fromisoformat(hash_data['last_login'])
            
            # ドライバーかどうかチェック
            if username.startswith('driver') and len(username) >= 6:
                # 24時間以内かチェック
                if last_login > datetime.now() - timedelta(days=1):
                    # TTLを更新（アクセス時に延長）
                    self.redis_client.expire(f"hash:{hashed_num}", 86400)
                    self.redis_client.expire(f"user:{username}", 86400)
                    return username
                else:
                    # 期限切れの場合は削除
                    self.delete_hash(hashed_num)
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to check hash {hashed_num}: {e}")
            return None
    
    def delete_hash(self, hashed_num: str) -> bool:
        """ハッシュを削除"""
        try:
            hash_data_str = self.redis_client.get(f"hash:{hashed_num}")
            if hash_data_str:
                hash_data = json.loads(hash_data_str)
                username = hash_data['username']
                # 両方向のキーを削除
                self.redis_client.delete(f"hash:{hashed_num}")
                self.redis_client.delete(f"user:{username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete hash {hashed_num}: {e}")
            return False
    
    def delete_user_hash(self, username: str) -> bool:
        """ユーザー名からハッシュを削除"""
        try:
            hashed_num = self.redis_client.get(f"user:{username}")
            if hashed_num:
                self.redis_client.delete(f"hash:{hashed_num}")
                self.redis_client.delete(f"user:{username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete user hash for {username}: {e}")
            return False
    
    def get_all_active_sessions(self):
        """全てのアクティブセッションを取得（デバッグ用）"""
        try:
            hash_keys = self.redis_client.keys("hash:*")
            sessions = []
            for key in hash_keys:
                data = self.redis_client.get(key)
                if data:
                    sessions.append({
                        'hash': key.split(':')[1],
                        'data': json.loads(data)
                    })
            return sessions
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []


# グローバルなRedisManager インスタンス
redis_manager = None

def get_redis_manager() -> RedisManager:
    """RedisManagerのシングルトンインスタンスを取得"""
    global redis_manager
    if redis_manager is None:
        redis_manager = RedisManager()
    return redis_manager

def init_redis_manager(app=None):
    """アプリケーション初期化時にRedisManagerを設定"""
    global redis_manager
    
    # 設定からRedis接続情報を取得（デフォルト値付き）
    if app:
        host = app.config.get('REDIS_HOST', 'localhost')
        port = app.config.get('REDIS_PORT', 6379)
        db = app.config.get('REDIS_DB', 1)
    else:
        host = 'localhost'
        port = 6379
        db = 1
    
    redis_manager = RedisManager(host=host, port=port, db=db)
    return redis_manager