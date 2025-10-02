import bcrypt
import secrets
import redis
import json
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, redirect, url_for, session, g, make_response

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
            db=int(os.getenv('REDIS_SESSION_DB', 1)),  # セッション用のDB
            decode_responses=True
        )
        self.session_timeout = int(os.getenv('SESSION_TIMEOUT', 3600))  # 1時間
    
    def create_session(self, user_id: int, user_data: dict) -> str:
        """
        セッション作成
        Returns: session_token
        """
        # セッショントークン生成
        session_token = secrets.token_hex(32)
        
        # セッションデータ
        session_data = {
            'user_id': user_id,
            'user_data': user_data,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()
        }
        
        # Redisに保存
        session_key = f"admin_session:{session_token}"
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
        
        session_key = f"admin_session:{session_token}"
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
        
        session_key = f"admin_session:{session_token}"
        return bool(self.redis_client.delete(session_key))
    
    def refresh_session(self, session_token: str) -> bool:
        """
        セッション期限延長
        """
        session_data = self.get_session(session_token)
        if not session_data:
            return False
        
        # 有効期限を更新
        session_data['expires_at'] = (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()
        
        session_key = f"admin_session:{session_token}"
        self.redis_client.setex(
            session_key,
            self.session_timeout,
            json.dumps(session_data)
        )
        
        return True
    
    def validate_session(self, session_token: str) -> dict:
        """
        セッション検証（有効期限も自動更新）
        """
        session_data = self.get_session(session_token)
        if session_data:
            self.refresh_session(session_token)
        return session_data

def login_required(f):
    """
    ログイン必須デコレータ
    セッションまたはCookieでの認証をチェック
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # セッションベースの認証をチェック
        user_id = session.get('user_id')
        if user_id:
            # セッションに基づいてユーザー情報を設定
            from app.models.user import User
            user = User.query.get(user_id)
            if user and user.is_active:
                g.current_user = user
                return f(*args, **kwargs)
        
        # Cookieベースの認証をチェック
        session_token = request.cookies.get('admin_session_token')
        if session_token:
            session_manager = SessionManager()
            session_data = session_manager.validate_session(session_token)
            
            if session_data:
                from app.models.user import User
                user = User.query.get(session_data['user_id'])
                if user and user.is_active:
                    g.current_user = user
                    # セッションにもユーザー情報を保存
                    session['user_id'] = user.id
                    return f(*args, **kwargs)
        
        # 認証されていない場合
        if request.is_json:
            # API リクエストの場合はJSONエラーを返す
            return jsonify({'error': 'Authentication required'}), 401
        else:
            # Webリクエストの場合は管理者ログインページにリダイレクト
            # 現在のURLがログインページでない場合のみリダイレクト
            if request.endpoint != 'index.login':
                return redirect(url_for('index.login'))
            else:
                # ログインページ自体で認証が必要な場合は、学生アプリにリダイレクト
                return redirect('https://localhost/')
    
    return decorated_function

def get_current_user():
    """
    現在ログイン中のユーザーを取得
    """
    return getattr(g, 'current_user', None)

def login_user(user, remember=False):
    """
    ユーザーをログイン状態にする
    """
    # セッションにユーザー情報を保存
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    
    # 永続化が必要な場合はCookieベースのセッション作成
    if remember:
        session_manager = SessionManager()
        user_data = {
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active
        }
        session_token = session_manager.create_session(user.id, user_data)
        return session_token
    
    return None

def logout_user():
    """
    ユーザーをログアウトする
    """
    # セッションからユーザー情報を削除
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    
    # Cookieベースのセッションも削除
    session_token = request.cookies.get('admin_session_token')
    if session_token:
        session_manager = SessionManager()
        session_manager.delete_session(session_token)
    
    # gからも削除
    g.current_user = None
    
    return session_token  # Cookieトークンを返す

def create_logout_response(redirect_url):
    """
    ログアウト用のレスポンスを作成（Cookieを削除）
    """
    response = make_response(redirect(redirect_url))
    response.set_cookie('admin_session_token', '', expires=0, httponly=True, secure=True)
    return response
