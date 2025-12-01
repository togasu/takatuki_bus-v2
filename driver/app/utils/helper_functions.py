"""ドライバーシステムのヘルパー関数群"""

from datetime import datetime, timedelta
from flask import request, g
from app.models import Driver
from app.database import db
import hashlib
import bcrypt
import random
import logging

logger = logging.getLogger('sojo-bus-log')

# Redis管理（開発環境用）
redis_manager = None
try:
    from app.utils.redis_manager_dev import redis_manager
    REDIS_AVAILABLE = True
    logger.info("Redis session management available (dev mode)")
except ImportError:
    REDIS_AVAILABLE = False
    logger.info("Redis not available, using fallback session management")


def add_cookie(key, value):
    """cookieに追加するための補助関数"""
    if not hasattr(g, 'cookies'):
        g.cookies = {}
    g.cookies[key] = value


def hash_login(username):
    """ログイン時にハッシュ化された番号を生成する関数（Redis対応+フォールバック）"""
    if REDIS_AVAILABLE:
        try:
            hashed_num = redis_manager.generate_hash_login(username)
            
            if hashed_num:
                add_cookie('hashed_num', hashed_num)
                logger.info(f"Hash login successful for user: {username} (Redis)")
                return hashed_num
        except Exception as e:
            logger.error(f"Redis hash login error for {username}: {e}")
    
    # フォールバック: 従来のセッション管理
    try:
        username_obj = db.session.query(Driver).filter_by(username=username).first()
        if not username_obj:
            return None
            
        hashed_string = username + str(random.randint(0, 1000000)) + str(datetime.now())
        hashed_num = hashlib.sha256(hashed_string.encode()).hexdigest()
        
        # セッションに保存（簡易的な実装）
        add_cookie('hashed_num', hashed_num)
        add_cookie('username', username)
        add_cookie('login_time', datetime.now().isoformat())
        
        logger.info(f"Hash login successful for user: {username} (fallback)")
        return hashed_num
        
    except Exception as e:
        logger.error(f"Fallback hash login error for {username}: {e}")
        return None


def hash_check(hashed_num):
    """ハッシュ化された番号をチェックする関数（Redis対応+フォールバック）"""
    if REDIS_AVAILABLE:
        try:
            username = redis_manager.check_hash(hashed_num)
            
            if username:
                logger.debug(f"Hash check successful for user: {username} (Redis)")
                return username
        except Exception as e:
            logger.error(f"Redis hash check error: {e}")
    
    # フォールバック: Cookieベースの検証
    try:
        username = request.cookies.get('username')
        login_time_str = request.cookies.get('login_time')
        
        if username and login_time_str:
            login_time = datetime.fromisoformat(login_time_str)
            # 24時間以内かチェック
            if login_time > datetime.now() - timedelta(days=1):
                if username.startswith('driver'):
                    logger.debug(f"Hash check successful for user: {username} (fallback)")
                    return username
        
        return None
        
    except Exception as e:
        logger.error(f"Fallback hash check error: {e}")
        return None


def verify_password(stored_password, stored_salt, provided_password):
    """passwordの暗号化の合致テスト（bcrypt使用）"""
    try:
        # bcrypt形式のハッシュを検証
        # stored_passwordにはすでにsaltが含まれているため、stored_saltは使用しない
        stored_hash_bytes = stored_password.encode('utf-8')
        provided_bytes = provided_password.encode('utf-8')
        return bcrypt.checkpw(provided_bytes, stored_hash_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def yukisaki(ud):
    """行き先の文字化"""
    if ud == 0:
        return "高槻キャンパス"
    else:
        return "高槻駅"


def gakusei(username):
    """学生番号のフォーマット"""
    if len(username) in [1, 2, 3, 4]:
        username = "driver" + username
    elif len(username) < 6:
        username = "使用不可"
    elif len(username) == 6:
        username = "情" + username[:2] + "-" + username[-4:]
    # 大学院生の場合
    elif str(username)[2] == "1":
        username = "情" + str(username[:2]) + "M" + str(username[4:])
    else:
        username = "情" + username[:2] + "D" + username[4:]
    return username


def get_authenticated_user():
    """認証されたユーザーを取得する"""
    # 優先順: Redis -> Cookieベースのフォールバック
    try:
        # Try Redis-based check first when available
        if REDIS_AVAILABLE:
            try:
                # If client provided a direct hashed_num cookie, check it in Redis
                hashed_num = request.cookies.get('hashed_num')
                if hashed_num:
                    username = redis_manager.check_hash(hashed_num)
                    if username:
                        logger.debug(f"Authenticated via Redis (hash): {username}")
                        return username

                # If username cookie exists (older fallback), try to resolve to a hash via Redis
                username_cookie = request.cookies.get('username')
                if username_cookie:
                    # redis_manager may provide a way to map user->hash; attempt if available
                    try:
                        hashed = None
                        rc = getattr(redis_manager, 'redis_client', None)
                        if rc:
                            hashed = rc.get(f"user:{username_cookie}")
                        if hashed:
                            username = redis_manager.check_hash(hashed)
                            if username:
                                logger.debug(f"Authenticated via Redis (username->hash): {username}")
                                return username
                    except Exception:
                        # ignore and fallback
                        pass

            except Exception as e:
                logger.error(f"Redis auth check failed: {e}")

        # Fallback: existing cookie-based check (may use Redis internally)
        hashed_num = request.cookies.get('hashed_num')
        if hashed_num:
            return hash_check(hashed_num)
        # 学生サービスが作成した driver_session_token を受け取る場合の互換処理
        driver_token = request.cookies.get('driver_session_token')
        if driver_token and isinstance(driver_token, str):
            # student.create_driver_session で生成されるフォーマット: "driver_<username>_<timestamp>"
            try:
                if driver_token.startswith('driver_'):
                    parts = driver_token.split('_')
                    if len(parts) >= 2:
                        username = parts[1]
                        if username.startswith('driver'):
                            logger.debug(f"Authenticated via driver_session_token: {username}")
                            return username
            except Exception:
                pass
    except Exception as e:
        logger.error(f"get_authenticated_user unexpected error: {e}")

    return None