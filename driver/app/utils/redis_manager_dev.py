"""Redis管理クラス（開発環境用シンプル実装）"""

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
    
    def check_hash(self, hashed_num: str) -> Optional[str]:
        """ハッシュからユーザー名を取得（ダミー実装）"""
        # 開発環境では常にdriver1を返す
        if hashed_num:
            return "driver1"
        return None
    
    def delete_user_hash(self, username: str) -> bool:
        """ユーザーのハッシュを削除（ダミー実装）"""
        return True
    
    def cleanup_expired_hashes(self) -> int:
        """期限切れハッシュをクリーンアップ（ダミー実装）"""
        return 0


# グローバルインスタンス
redis_manager = RedisManager()