"""
Student Service Configuration
環境変数から設定を読み込みます
"""
import os

# ===================================
# 外部API設定
# ===================================
API_URL = os.getenv('API_URL', 'http://192.168.100.5:49155')
REGIST_API = os.getenv('REGIST_API', 'http://192.168.100.5:49160')

# ===================================
# サービス間接続設定
# ===================================
ADMIN_SERVICE_HOST = os.getenv('ADMIN_SERVICE_HOST', 'admin')
ADMIN_SERVICE_PORT = os.getenv('ADMIN_SERVICE_PORT', '5000')
DRIVER_SERVICE_HOST = os.getenv('DRIVER_SERVICE_HOST', 'driver')
DRIVER_SERVICE_PORT = os.getenv('DRIVER_SERVICE_PORT', '5001')

# ===================================
# データベース設定
# ===================================
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'mydb')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'pass')

# ===================================
# Redis設定
# ===================================
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
REDIS_URL = os.getenv('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')

# ===================================
# LDAP設定
# ===================================
LDAP_SERVER = os.getenv('LDAP_SERVER', 'ldap://tcs11.edu.kutc.kansai-u.ac.jp')
LDAP_BASE_DN = os.getenv('LDAP_BASE_DN', 'dc=kutc,dc=kansai-u,dc=ac,dc=jp')
LDAP_USER_DN_TEMPLATE = os.getenv('LDAP_USER_DN_TEMPLATE', 'uid={username},ou=People,dc=kutc,dc=kansai-u,dc=ac,dc=jp')

# ===================================
# セキュリティ設定
# ===================================
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
ADMIN_SERVICE_TOKEN = os.getenv('ADMIN_SERVICE_TOKEN', 'admin-secret-token-2024')
API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'bus-system-api-key-2024')

# Auth System APIキー（バス車内認証システム専用）
AUTH_SYSTEM_API_KEY = os.getenv('AUTH_SYSTEM_API_KEY', 'auth-system-secret-key-2024-change-in-production')

# Cookie設定
COOKIE_DOMAIN = os.getenv('COOKIE_DOMAIN', 'localhost')
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Strict')

# ===================================
# アプリケーション設定
# ===================================
# バス設定
MAX_SEATS = 27

# セッション設定
SESSION_TIMEOUT_MINUTES = 15

# リクエストタイムアウト（秒）
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '10'))

# ログ設定
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', '/app/logs/student.log')

# Flask設定
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

# Rate Limiting設定
RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'true').lower() == 'true'
RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', REDIS_URL)
