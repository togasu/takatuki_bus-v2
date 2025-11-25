# 設定管理ベストプラクティス

## 概要

このプロジェクトでは、各サービスの設定を`config.py`で一元管理しています。これにより、コードの可読性と保守性が向上します。

## アーキテクチャ

```
各サービス/
├── app/
│   ├── config.py          # 設定の一元管理
│   ├── __init__.py         # configをインポート
│   └── routes/
│       └── *.py           # configをインポートして使用
└── .env                   # 環境変数ファイル
```

## 使用方法

### 設定ファイルの作成

各サービスの`app/config.py`で環境変数を読み込みます：

```python
"""
Student Service Configuration
環境変数から設定を読み込みます
"""
import os

# データベース設定
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'mydb')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'pass')

# Redis設定
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_URL = os.getenv('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}')
```

### コード内での使用

#### ❌ **非推奨**: 各ファイルで個別に環境変数を読み込む

```python
# 可読性が低く、重複コードが多い
import os

API_URL = os.getenv('API_URL', 'http://192.168.100.5:49155')
ADMIN_SERVICE_HOST = os.getenv('ADMIN_SERVICE_HOST', 'admin')
ADMIN_SERVICE_PORT = os.getenv('ADMIN_SERVICE_PORT', '5000')

def some_function():
    url = f"http://{ADMIN_SERVICE_HOST}:{ADMIN_SERVICE_PORT}/api"
    # ...
```

#### ✅ **推奨**: configモジュールから読み込む

```python
# 可読性が高く、一元管理されている
from .. import config

def some_function():
    url = f"http://{config.ADMIN_SERVICE_HOST}:{config.ADMIN_SERVICE_PORT}/api"
    # ...
```

## メリット

### 1. **可読性の向上**
- 設定がどこで定義されているか明確
- `config.VARIABLE_NAME` で設定の参照が一目瞭然

### 2. **保守性の向上**
- 設定の変更が1か所で完結
- デフォルト値の管理が容易

### 3. **テストの容易性**
- モックが簡単
- 設定の上書きが可能

```python
# テストコード例
from unittest.mock import patch

def test_function():
    with patch('app.config.ADMIN_SERVICE_HOST', 'test-admin'):
        # テストコード
        pass
```

### 4. **型安全性**
- 型変換を1か所で実施
- 間違った型の使用を防止

```python
# config.py
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))  # 必ずint型

# 使用側
redis.connect(host=config.REDIS_HOST, port=config.REDIS_PORT)  # 型エラーなし
```

## 設定の分類

### アプリケーション設定
- ビジネスロジックに関する設定
- デフォルト値を持つ

```python
# バス設定
MAX_SEATS = 27

# セッション設定
SESSION_TIMEOUT_MINUTES = 15
```

### 環境依存設定
- 環境変数から読み込む
- 本番/開発で値が異なる

```python
# データベース接続
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'pass')

# セキュリティ
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
```

## ベストプラクティス

### 1. デフォルト値の設定

開発環境で動作するデフォルト値を設定：

```python
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')  # Docker Compose用
```

### 2. 型変換の実施

環境変数は文字列なので、必要に応じて型変換：

```python
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
```

### 3. 複合設定の構築

基本設定から複合設定を構築：

```python
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))

# 複合設定
REDIS_URL = os.getenv('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')
```

### 4. ドキュメント化

設定の目的をコメントで明記：

```python
# ===================================
# セキュリティ設定
# ===================================
# Cookie設定
COOKIE_DOMAIN = os.getenv('COOKIE_DOMAIN', 'localhost')
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true'  # HTTPS必須
SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'  # XSS対策
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Strict')  # CSRF対策
```

## 各サービスの設定ファイル

### Student Service
`student/app/config.py`
- 外部API設定（LDAP、登録API）
- 他サービス接続設定
- セッション管理設定

### Admin Service
`admin/app/config.py`
- 権限管理設定
- マイグレーション設定
- 管理者認証設定

### Driver Service
`driver/app/config.py`
- ドライバー管理設定
- 位置情報設定
- 運行管理設定

## トラブルシューティング

### 設定が反映されない

1. `.env`ファイルが正しい場所にあるか確認
2. Docker コンテナを再起動

```powershell
docker-compose down
docker-compose up -d
```

### import エラー

```python
# NG
from config import REDIS_HOST  # config.pyがapp/の下にある場合

# OK
from . import config  # 相対インポート
from app import config  # 絶対インポート
```

## 参考

- [環境変数設定ガイド](./environment-variables.md)
- [12-Factor App: Config](https://12factor.net/config)
- [Flask Configuration Handling](https://flask.palletsprojects.com/en/2.3.x/config/)
