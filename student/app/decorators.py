"""
認証デコレーター
内部APIへのアクセスを制限するためのデコレーター
"""

from functools import wraps
from flask import request, jsonify, current_app
import os
import logging

logger = logging.getLogger(__name__)

def require_service_auth(f):
    """
    内部サービス認証デコレーター
    X-Service-Authヘッダーで認証を行う
    adminサービスなど信頼できる内部サービスからのアクセスのみ許可
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # リクエストヘッダーから認証トークンを取得
        service_auth_token = request.headers.get('X-Service-Auth')
        api_key = request.headers.get('X-API-Key')
        
        # 環境変数から正しいトークンを取得
        expected_token = os.getenv('ADMIN_SERVICE_TOKEN', 'admin-secret-token-2024')
        expected_api_key = os.getenv('API_SECRET_KEY', 'bus-system-api-key-2024')
        
        # トークンの検証
        if not service_auth_token or service_auth_token != expected_token:
            logger.warning(f"Unauthorized internal API access attempt from {request.remote_addr}")
            return jsonify({
                'success': False,
                'message': 'Unauthorized: Invalid service authentication token'
            }), 401
        
        # API Keyの検証（オプション、より強固なセキュリティのため）
        if not api_key or api_key != expected_api_key:
            logger.warning(f"Unauthorized internal API access attempt (invalid API key) from {request.remote_addr}")
            return jsonify({
                'success': False,
                'message': 'Unauthorized: Invalid API key'
            }), 401
        
        logger.info(f"Internal API access authenticated from {request.remote_addr}")
        return f(*args, **kwargs)
    
    return decorated_function
