import redis
import time
import uuid
from contextlib import contextmanager

class RedisLock:
    def __init__(self, redis_client, key, timeout=10, retry_delay=0.1):
        self.redis_client = redis_client
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.identifier = str(uuid.uuid4())
    
    def acquire(self):
        """ロックを取得する"""
        end_time = time.time() + self.timeout
        while time.time() < end_time:
            if self.redis_client.set(self.key, self.identifier, nx=True, ex=self.timeout):
                return True
            time.sleep(self.retry_delay)
        return False
    
    def release(self):
        """ロックを解放する"""
        # Luaスクリプトを使用してアトミックにロックを解放
        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        return self.redis_client.eval(lua_script, 1, self.key, self.identifier)

@contextmanager
def redis_lock(redis_client, key, timeout=10, retry_delay=0.1):
    """Redisロックのコンテキストマネージャー"""
    lock = RedisLock(redis_client, key, timeout, retry_delay)
    try:
        if lock.acquire():
            yield lock
        else:
            raise TimeoutError(f"ロックの取得に失敗しました: {key}")
    finally:
        lock.release()

def get_redis_client():
    """Redis接続を取得"""
    try:
        redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        redis_client.ping()  # 接続確認
        return redis_client
    except Exception as e:
        print(f"Redis接続エラー: {e}")
        return None