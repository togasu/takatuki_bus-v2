"""
エラーハンドリング用のユーティリティモジュール
"""
from flask import jsonify, request, current_app, render_template
import logging
import traceback
from werkzeug.exceptions import HTTPException
import psycopg2
import redis
from app.utils.helper_functions import get_authenticated_user

class ErrorLogger:
    """エラーログを記録するクラス"""
    
    @staticmethod
    def log_error(error, request_info=None):
        """エラーをログに記録"""
        if request_info is None:
            request_info = {
                'method': request.method if request else 'UNKNOWN',
                'url': request.url if request else 'UNKNOWN',
                'remote_addr': request.remote_addr if request else 'UNKNOWN',
                'user_agent': request.user_agent.string if request and request.user_agent else 'UNKNOWN'
            }
        
        error_message = f"""
ERROR: {str(error)}
METHOD: {request_info['method']}
URL: {request_info['url']}
IP: {request_info['remote_addr']}
USER_AGENT: {request_info['user_agent']}
TRACEBACK: {traceback.format_exc()}
        """
        
        current_app.logger.error(error_message)

def create_error_response(message, status_code=500, error_type="Internal Server Error"):
    """標準的なエラーレスポンスを作成"""
    return jsonify({
        "error": True,
        "error_type": error_type,
        "message": message,
        "status_code": status_code
    }), status_code

def handle_database_error(error):
    """データベースエラーのハンドリング"""
    ErrorLogger.log_error(error)
    
    if isinstance(error, psycopg2.IntegrityError):
        return create_error_response(
            "データの整合性エラーが発生しました",
            400,
            "Database Integrity Error"
        )
    elif isinstance(error, psycopg2.OperationalError):
        return create_error_response(
            "データベース接続エラーが発生しました",
            503,
            "Database Connection Error"
        )
    else:
        return create_error_response(
            "データベースエラーが発生しました",
            500,
            "Database Error"
        )

def handle_redis_error(error):
    """Redisエラーのハンドリング"""
    ErrorLogger.log_error(error)
    return create_error_response(
        "セッションサービスエラーが発生しました",
        503,
        "Session Service Error"
    )

def handle_validation_error(error):
    """バリデーションエラーのハンドリング"""
    return create_error_response(
        str(error),
        400,
        "Validation Error"
    )

def handle_authentication_error(error):
    """認証エラーのハンドリング"""
    return create_error_response(
        "認証に失敗しました",
        401,
        "Authentication Error"
    )

def handle_authorization_error(error):
    """認可エラーのハンドリング"""
    return create_error_response(
        "このリソースにアクセスする権限がありません",
        403,
        "Authorization Error"
    )

def handle_not_found_error(error):
    """リソースが見つからないエラーのハンドリング"""
    return create_error_response(
        "要求されたリソースが見つかりません",
        404,
        "Not Found"
    )

def handle_method_not_allowed_error(error):
    """許可されていないメソッドエラーのハンドリング"""
    return create_error_response(
        "このメソッドは許可されていません",
        405,
        "Method Not Allowed"
    )

def handle_rate_limit_error(error):
    """レート制限エラーのハンドリング"""
    return create_error_response(
        "リクエストが多すぎます。しばらく待ってから再試行してください",
        429,
        "Too Many Requests"
    )

def register_error_handlers(app):
    """Flaskアプリにエラーハンドラーを登録"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return handle_validation_error("不正なリクエストです")
    
    @app.errorhandler(401)
    def unauthorized(error):
        return handle_authentication_error("認証が必要です")
    
    @app.errorhandler(403)
    def forbidden(error):
        return handle_authorization_error("アクセスが拒否されました")
    
    @app.errorhandler(404)
    def not_found(error):
        return handle_not_found_error("ページが見つかりません")
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return handle_method_not_allowed_error("許可されていないメソッドです")
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return handle_rate_limit_error("リクエスト制限に達しました")
    
    @app.errorhandler(500)
    def internal_server_error(error):
        ErrorLogger.log_error(error)
        return create_error_response(
            "内部サーバーエラーが発生しました",
            500,
            "Internal Server Error"
        )
    
    @app.errorhandler(503)
    def service_unavailable(error):
        ErrorLogger.log_error(error)
        return create_error_response(
            "サービスが一時的に利用できません",
            503,
            "Service Unavailable"
        )
    
    @app.errorhandler(psycopg2.Error)
    def handle_postgres_error(error):
        return handle_database_error(error)
    
    @app.errorhandler(redis.RedisError)
    def handle_redis_exception(error):
        return handle_redis_error(error)
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        ErrorLogger.log_error(error)
        return create_error_response(
            "予期しないエラーが発生しました",
            500,
            "Unexpected Error"
        )

class SafeExecutor:
    """安全な実行を提供するクラス"""
    
    @staticmethod
    def execute_with_error_handling(func, *args, **kwargs):
        """エラーハンドリング付きで関数を実行"""
        try:
            return func(*args, **kwargs)
        except psycopg2.Error as e:
            return handle_database_error(e)
        except redis.RedisError as e:
            return handle_redis_error(e)
        except ValueError as e:
            return handle_validation_error(e)
        except Exception as e:
            ErrorLogger.log_error(e)
            return create_error_response(
                "処理中にエラーが発生しました",
                500,
                "Processing Error"
            )


def topview_with_message(message):
    """認証済みユーザー向けのトップページビューを返す"""
    from app.services import DriverService
    
    user = get_authenticated_user()
    if not user:
        return render_template('login.html')
    
    firstbus, secondbus = DriverService.create_driver_buses_info(user)
    return render_template('top.html', firstbus=firstbus, secoundbus=secondbus, message=message)


def register_driver_error_handlers(app):
    """ドライバーシステム用のエラーハンドラーを登録"""
    
    @app.errorhandler(400)
    def bad_request(e):
        user = get_authenticated_user()
        if user:
            return topview_with_message('想定しない動作が行われました')
        return render_template('login.html')

    @app.errorhandler(404)
    def not_found(e):
        user = get_authenticated_user()
        if user:
            return topview_with_message('ページが見つかりません')
        return render_template('login.html')

    @app.errorhandler(405)
    def not_allowed(e):
        user = get_authenticated_user()
        if user:
            return topview_with_message('値がありません')
        return render_template('login.html')

    @app.errorhandler(500)
    def internal_server_error(e):
        user = get_authenticated_user()
        if user:
            return topview_with_message('サーバー内部エラー')
        return render_template('login.html')
