"""ドライバーシステムのヘルパー関数群"""

from datetime import datetime, timedelta
from flask import request, g
from app.models import Driver
from app.database import db
import hashlib
import random
import logging

logger = logging.getLogger('sojo-bus-log')

# Redis管理（開発環境用）
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
    """passwordの暗号化の合致テスト"""
    library_hashed = hashlib.pbkdf2_hmac(
        'sha256', provided_password.encode('utf-8'), stored_salt, 1000
    )
    return library_hashed == stored_password


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
    hashed_num = request.cookies.get('hashed_num')
    if hashed_num:
        return hash_check(hashed_num)
    return None