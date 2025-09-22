"""
安全なルート実行のためのデコレータ
"""
from functools import wraps
from flask import jsonify, request, current_app
from .error_handlers import ErrorLogger, create_error_response, handle_database_error, handle_redis_error, handle_validation_error
import psycopg2
import redis

def safe_route(f):
    """ルートを安全に実行するデコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except psycopg2.IntegrityError as e:
            return handle_database_error(e)
        except psycopg2.OperationalError as e:
            return handle_database_error(e)
        except psycopg2.Error as e:
            return handle_database_error(e)
        except redis.RedisError as e:
            return handle_redis_error(e)
        except ValueError as e:
            return handle_validation_error(e)
        except KeyError as e:
            return create_error_response(
                f"必要なパラメータが不足しています: {str(e)}",
                400,
                "Missing Parameter"
            )
        except TypeError as e:
            return create_error_response(
                f"パラメータの型が正しくありません: {str(e)}",
                400,
                "Type Error"
            )
        except Exception as e:
            ErrorLogger.log_error(e)
            return create_error_response(
                "予期しないエラーが発生しました",
                500,
                "Unexpected Error"
            )
    
    return decorated_function

def validate_json_data(required_fields=None, optional_fields=None):
    """JSONデータのバリデーションを行うデコレータ"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                
                if data is None:
                    return create_error_response(
                        "JSONデータが必要です",
                        400,
                        "Missing JSON Data"
                    )
                
                # 必須フィールドのチェック
                if required_fields:
                    for field in required_fields:
                        if field not in data:
                            return create_error_response(
                                f"必須フィールド '{field}' が不足しています",
                                400,
                                "Missing Required Field"
                            )
                        
                        # 空文字列や None のチェック
                        if data[field] is None or (isinstance(data[field], str) and data[field].strip() == ""):
                            return create_error_response(
                                f"フィールド '{field}' が空です",
                                400,
                                "Empty Required Field"
                            )
                
                return f(*args, **kwargs)
                
            except Exception as e:
                ErrorLogger.log_error(e)
                return create_error_response(
                    "リクエストデータの処理中にエラーが発生しました",
                    400,
                    "Request Processing Error"
                )
        
        return decorated_function
    return decorator

def require_auth_token(f):
    """認証トークンを要求するデコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('X-Service-Auth')
            
            if not auth_header:
                return create_error_response(
                    "認証トークンが必要です",
                    401,
                    "Missing Auth Token"
                )
            
            # トークンの検証はここで行う（実際の実装では SessionManager を使用）
            return f(*args, **kwargs)
            
        except Exception as e:
            ErrorLogger.log_error(e)
            return create_error_response(
                "認証処理中にエラーが発生しました",
                401,
                "Authentication Error"
            )
    
    return decorated_function

def rate_limit(max_requests=60, window_seconds=60):
    """レート制限を行うデコレータ（簡易版）"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 実際の実装では Redis や メモリベースのレート制限を実装
            # ここでは基本的な実装のみ
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_request(f):
    """リクエストをログに記録するデコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            current_app.logger.info(f"REQUEST: {request.method} {request.url} from {request.remote_addr}")
            result = f(*args, **kwargs)
            current_app.logger.info(f"RESPONSE: {request.method} {request.url} completed successfully")
            return result
        except Exception as e:
            current_app.logger.error(f"REQUEST: {request.method} {request.url} failed with error: {str(e)}")
            raise
    
    return decorated_function

def safe_api_route(required_fields=None, require_auth=False, max_requests=None):
    """APIルート用の包括的なデコレータ"""
    def decorator(f):
        @wraps(f)
        @safe_route
        @log_request
        def decorated_function(*args, **kwargs):
            # 認証チェック
            if require_auth:
                auth_header = request.headers.get('X-Service-Auth')
                if not auth_header:
                    return create_error_response(
                        "認証トークンが必要です",
                        401,
                        "Missing Auth Token"
                    )
            
            # JSONデータのバリデーション
            if required_fields and request.method in ['POST', 'PUT', 'PATCH']:
                data = request.get_json()
                
                if data is None:
                    return create_error_response(
                        "JSONデータが必要です",
                        400,
                        "Missing JSON Data"
                    )
                
                for field in required_fields:
                    if field not in data:
                        return create_error_response(
                            f"必須フィールド '{field}' が不足しています",
                            400,
                            "Missing Required Field"
                        )
                    
                    if data[field] is None or (isinstance(data[field], str) and data[field].strip() == ""):
                        return create_error_response(
                            f"フィールド '{field}' が空です",
                            400,
                            "Empty Required Field"
                        )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def admin_required(f):
    """管理者権限が必要なルートに使用するデコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 簡単な認証チェック（実際の認証システムに応じて調整）
            # 現在はセッションベースの認証を想定
            from flask import session
            
            # セッションチェック
            if 'user_id' not in session:
                from flask import redirect, url_for
                return redirect(url_for('index.login'))
            
            # 管理者権限チェック（必要に応じて追加）
            user_role = session.get('role', '')
            if user_role not in ['admin', 'super_admin']:
                return create_error_response(
                    "管理者権限が必要です",
                    403,
                    "Admin Access Required"
                )
            
            return f(*args, **kwargs)
            
        except Exception as e:
            ErrorLogger.log_error(e)
            return create_error_response(
                "認証処理でエラーが発生しました",
                500,
                "Authentication Error"
            )
    
    return decorated_function
