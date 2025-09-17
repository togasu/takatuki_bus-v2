from functools import wraps
from flask import request, jsonify
import os

def admin_required(f):
    """
    API関数へのアクセスをadminサービスからのみに制限するデコレータ
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # リクエストヘッダーから認証情報を取得
        auth_header = request.headers.get('X-Service-Auth')
        
        # 環境変数から管理者用の認証トークンを取得（本番環境では強力なトークンを使用）
        admin_token = os.getenv('ADMIN_SERVICE_TOKEN', 'admin-secret-token-2024')
        
        # 認証トークンの検証
        if not auth_header or auth_header != admin_token:
            return jsonify({
                'error': 'Unauthorized access',
                'message': 'API access is restricted to admin service only'
            }), 403
        
        # User-Agentでサービス識別も追加チェック
        user_agent = request.headers.get('User-Agent', '')
        if 'admin-service' not in user_agent.lower():
            return jsonify({
                'error': 'Forbidden',
                'message': 'Invalid service identifier'
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function

def validate_admin_access():
    """
    管理者サービスからのアクセスかどうかを検証する関数
    """
    # X-Forwarded-Forヘッダーから送信元IPを確認
    forwarded_for = request.headers.get('X-Forwarded-For')
    real_ip = request.headers.get('X-Real-IP')
    
    # Dockerネットワーク内からのアクセスかチェック
    # 本番環境では具体的なIPレンジを指定
    allowed_sources = ['admin', 'localhost', '127.0.0.1']
    
    if forwarded_for:
        # adminサービスからのリクエストかチェック
        if any(source in forwarded_for for source in allowed_sources):
            return True
    
    return False

def require_api_key(f):
    """
    APIキーベースの認証デコレータ
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        # 環境変数からAPIキーを取得
        valid_api_key = os.getenv('API_SECRET_KEY', 'bus-system-api-key-2024')
        
        if not api_key or api_key != valid_api_key:
            return jsonify({
                'error': 'Invalid API Key',
                'message': 'Valid API key required for access'
            }), 401
            
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """
    現在のユーザーを取得する関数
    セッショントークンからユーザー情報を取得
    """
    from app.utils.auth_utils import SessionManager
    from flask import session, g
    
    # まずgオブジェクトから取得を試行
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user
    
    # セッションからユーザーIDを取得
    user_id = session.get('user_id')
    if user_id:
        try:
            from app.models.user import User
            user = User.query.get(user_id)
            if user and user.is_active:
                g.current_user = user
                return user
        except Exception:
            pass
    
    # リクエストヘッダーからセッショントークンを取得（API用）
    auth_header = request.headers.get('X-Service-Auth')
    
    if auth_header:
        # セッションマネージャーでトークンを検証
        session_manager = SessionManager()
        session_data = session_manager.validate_session(auth_header)
        
        if session_data:
            # セッションデータからユーザー情報を取得
            user_id = session_data.get('user_id')
            if user_id:
                try:
                    from app.models.user import User
                    user = User.query.get(user_id)
                    if user and user.is_active:
                        g.current_user = user
                        return user
                except Exception:
                    pass
    
    # Cookieからセッショントークンを取得
    session_token = request.cookies.get('admin_session_token')
    if session_token:
        session_manager = SessionManager()
        session_data = session_manager.validate_session(session_token)
        
        if session_data:
            user_id = session_data.get('user_id')
            if user_id:
                try:
                    from app.models.user import User
                    user = User.query.get(user_id)
                    if user and user.is_active:
                        g.current_user = user
                        # セッションにもユーザー情報を保存
                        session['user_id'] = user.id
                        return user
                except Exception:
                    pass
    
    return None
