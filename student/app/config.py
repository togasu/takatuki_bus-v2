# API設定
API_URL = "http://192.168.100.5:49155"
REGIST_API = "http://192.168.100.5:49160"

# 開発環境用設定（コメントアウト）
# API_URL = "http://localhost:5000"
# REGIST_API = "http://localhost:5000"

# バス設定
MAX_SEATS = 27

# セッション設定
SESSION_TIMEOUT_MINUTES = 15

# Redis設定
import os
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')  # パスワードが必要な場合は環境変数で設定

# LDAP設定
LDAP_SERVER = os.getenv('LDAP_SERVER', 'ldap://tcs11.edu.kutc.kansai-u.ac.jp')
LDAP_BASE_DN = os.getenv('LDAP_BASE_DN', 'dc=kutc,dc=kansai-u,dc=ac,dc=jp')
LDAP_USER_DN_TEMPLATE = os.getenv('LDAP_USER_DN_TEMPLATE', 'uid={username},ou=People,dc=kutc,dc=kansai-u,dc=ac,dc=jp')