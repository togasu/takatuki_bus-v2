# 環境変数設定ガイド

## 概要

このプロジェクトでは、環境変数を使用してセキュリティ設定やサービス間の接続情報を管理しています。

## ファイル構成

```
takatuki_bus-v2/
├── .env                    # プロジェクト全体の環境変数
├── .env.example            # 環境変数のテンプレート（Git管理対象）
├── student/.env            # Student サービス固有の環境変数
├── admin/.env              # Admin サービス固有の環境変数
└── driver/.env             # Driver サービス固有の環境変数
```

## セットアップ手順

### 1. 開発環境のセットアップ

既に `.env` ファイルが作成されています。そのまま使用できます。

### 2. 新規セットアップの場合

`.env.example` をコピーして使用します：

```powershell
# PowerShell
Copy-Item .env.example .env
```

### 3. 本番環境のセットアップ

**重要:** 本番環境では必ず以下の値を変更してください：

```env
# セキュリティトークン（ランダムな文字列に変更）
ADMIN_SERVICE_TOKEN=your-secure-random-token-here
API_SECRET_KEY=your-secure-api-key-here

# データベースパスワード
POSTGRES_PASSWORD=your-secure-db-password

# Cookie設定（本番ドメインに変更）
COOKIE_DOMAIN=yourdomain.com

# 環境設定
ENVIRONMENT=production
```

## 環境変数一覧

### 共通設定（.env）

| 変数名 | 説明 | デフォルト値 | 必須 |
|--------|------|-------------|------|
| `ENVIRONMENT` | 実行環境 (development/production) | `development` | ○ |
| `SKIP_MIGRATION` | マイグレーションをスキップ | `false` | × |
| `POSTGRES_HOST` | PostgreSQLホスト | `postgres` | ○ |
| `POSTGRES_DB` | データベース名 | `mydb` | ○ |
| `POSTGRES_USER` | データベースユーザー | `user` | ○ |
| `POSTGRES_PASSWORD` | データベースパスワード | `pass` | ○ |
| `REDIS_HOST` | Redisホスト | `redis` | ○ |
| `REDIS_PORT` | Redisポート | `6379` | ○ |
| `ADMIN_SERVICE_TOKEN` | Admin サービス認証トークン | - | ○ |
| `API_SECRET_KEY` | API シークレットキー | - | ○ |
| `REQUEST_TIMEOUT` | APIリクエストタイムアウト（秒） | `10` | × |
| `COOKIE_DOMAIN` | Cookie のドメイン | `localhost` | ○ |
| `LOG_LEVEL` | ログレベル (DEBUG/INFO/WARNING/ERROR) | `INFO` | × |

### Student サービス固有設定（student/.env）

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `API_URL` | 外部API URL | `http://192.168.100.5:49155` |
| `REGIST_API` | 登録API URL | `http://192.168.100.5:49160` |
| `ADMIN_SERVICE_HOST` | Admin サービスホスト | `admin` |
| `ADMIN_SERVICE_PORT` | Admin サービスポート | `5000` |
| `DRIVER_SERVICE_HOST` | Driver サービスホスト | `driver` |
| `DRIVER_SERVICE_PORT` | Driver サービスポート | `5001` |

### セキュリティ設定

すべてのサービスで以下のセキュリティ設定が有効です：

```env
# Cookie セキュリティ
SESSION_COOKIE_SECURE=true      # HTTPS のみ
SESSION_COOKIE_HTTPONLY=true    # JavaScript からアクセス不可
SESSION_COOKIE_SAMESITE=Strict  # CSRF 対策

# Rate Limiting
RATELIMIT_ENABLED=true
RATELIMIT_STORAGE_URL=redis://redis:6379
```

## セキュアなトークンの生成方法

### PowerShell

```powershell
# ランダムな32文字のトークン生成
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

### Python

```python
import secrets
print(secrets.token_urlsafe(32))
```

### OpenSSL

```bash
openssl rand -base64 32
```

## 使用例

### Docker Compose で使用

```powershell
# 環境変数を読み込んでコンテナ起動
docker-compose up -d
```

### 環境変数の確認

```powershell
# 特定のサービスの環境変数を確認
docker-compose config | Select-String -Pattern "student:" -Context 0,20
```

## トラブルシューティング

### 環境変数が反映されない

1. `.env` ファイルが正しい場所にあるか確認
2. Docker コンテナを再起動

```powershell
docker-compose down
docker-compose up -d
```

### 本番環境でのチェックリスト

- [ ] `ADMIN_SERVICE_TOKEN` を変更
- [ ] `API_SECRET_KEY` を変更
- [ ] `POSTGRES_PASSWORD` を変更
- [ ] `SECRET_KEY` (各サービス) を変更
- [ ] `COOKIE_DOMAIN` を本番ドメインに設定
- [ ] `ENVIRONMENT=production` に設定
- [ ] `FLASK_DEBUG=false` を確認
- [ ] `SESSION_COOKIE_SECURE=true` を確認

## セキュリティ上の注意

⚠️ **重要:**

1. `.env` ファイルは **絶対に Git にコミットしない**
2. 本番環境では **必ずすべてのトークンを変更**
3. パスワードは **強力なものを使用**（最低12文字、英数字記号混在）
4. 環境変数ファイルのパーミッションを適切に設定

```bash
# Linux/Mac の場合
chmod 600 .env
chmod 600 student/.env
chmod 600 admin/.env
chmod 600 driver/.env
```

## 参考

- [Flask Configuration](https://flask.palletsprojects.com/en/2.3.x/config/)
- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [12-Factor App: Config](https://12factor.net/config)
