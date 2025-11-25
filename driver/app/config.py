"""
Driver Service Configuration
環境変数から設定を読み込みます
"""
import os

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
# セキュリティ設定
# ===================================
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
ADMIN_SERVICE_TOKEN = os.getenv('ADMIN_SERVICE_TOKEN', 'admin-secret-token-2024')
API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'bus-system-api-key-2024')

# Cookie設定
COOKIE_DOMAIN = os.getenv('COOKIE_DOMAIN', 'localhost')
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Strict')

# ===================================
# アプリケーション設定
# ===================================
# リクエストタイムアウト（秒）
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '10'))

# ログ設定
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', '/app/logs/driver.log')

# Flask設定
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

# マイグレーション設定
SKIP_MIGRATION = os.getenv('SKIP_MIGRATION', 'false').lower() == 'true'
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Rate Limiting設定
RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'true').lower() == 'true'
RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', REDIS_URL)
