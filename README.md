# Takatsuki-bus system v2

## 概要

このプロジェクトは、**Flaskベースのマイクロサービス**（`student` / `admin` / `driver`）を  
**nginx リバースプロキシ**で統合し、**PostgreSQL** と **Redis** をバックエンドに利用するバス予約管理システムです。

## 主な機能

- **学生向けバス予約システム** - LDAP認証による予約・キャンセル管理
- **管理者向け管理画面** - 学生・ドライバー・バス管理、ペナルティシステム、学期管理
- **ドライバー向け運行管理** - 予約確認・承認、Q&A機能
- **WebSocket対応** - リアルタイム通知とメッセージング
- **権限管理システム** - 3段階の権限レベル（Guest/Normal/Admin）
- **自動ペナルティシステム** - 未乗車3回で自動ペナルティ適用
- **学期管理システム** - 日付ベースの学期切り替えとユーザーデータ移行

## システム構成

```
.
├── student/          # 学生向けバス予約サービス
├── admin/            # 管理者向け管理画面
├── driver/           # ドライバー向け運行管理
├── nginx/            # リバースプロキシ設定
├── certs/            # SSL証明書
├── logs/             # アクセスログ
├── docs/             # 詳細ドキュメント
└── docker-compose.yml
```

## クイックスタート

### 前提条件
- Docker / Docker Compose がインストールされていること
- OpenSSL が利用可能であること

### 1. システム起動

#### Windows PowerShell
```powershell
# 通常起動（既存のデータベースを保持）
.\start-dev.ps1

# データベース初期化して起動
.\start-dev.ps1 init

# データベース初期化 + テストデータ作成
.\start-dev.ps1 init debug
```

#### Mac / Linux / WSL
```bash
# 通常起動
./start-dev.sh

# データベース初期化して起動
./start-dev.sh init

# データベース初期化 + テストデータ作成
./start-dev.sh init debug
```

### 2. アクセス

起動後、以下のURLからアクセスできます：

- **🎓 学生用システム**: https://localhost/student
- **🔧 管理画面**: https://localhost/admin
- **🚛 ドライバー画面**: https://localhost/driver

### 3. 認証情報

#### 学生ユーザー
- **ユーザー名**: k番号（例: k123456）
- **認証方式**: LDAP認証

#### 管理者（デバッグモード時）
- **ユーザー名**: admin_test
- **パスワード**: admin123

#### ドライバー（デバッグモード時）
- **ユーザー名**: driver_test
- **パスワード**: driver123

## ドキュメント

詳細なドキュメントは `docs/` ディレクトリにあります：

### セットアップ・運用
- [起動ガイド](docs/startup-guide.md) - システムの起動方法と基本操作
- [エラーハンドリング](docs/error-handling.md) - エラー処理とトラブルシューティング

### 機能別ガイド
- [ペナルティシステム](docs/penalty-system.md) - ペナルティ機能の詳細説明
- [ペナルティクイックスタート](docs/penalty-quickstart.md) - ペナルティ機能の使い方
- [学期管理システム](docs/semester-management.md) - 学期管理の詳細説明
- [学期管理GUI操作](docs/semester-gui-guide.md) - 学期管理画面の使い方
- [権限システム](docs/permissions-system.md) - 権限管理の詳細説明

### サービス別ドキュメント
- [Student Service](docs/student-service.md) - 学生向けサービスの詳細
- [Admin Service](docs/admin-service.md) - 管理者サービスの詳細
- [Driver Service](docs/driver-service.md) - ドライバーサービスの詳細

### セキュリティ
- [内部APIセキュリティ](docs/internal-api-security.md) - マイクロサービス間API保護の詳細

### 開発者向け
- [Admin Migration Guide](docs/admin-migration.md) - Admin サービスのマイグレーション
- [Driver Migration Guide](docs/driver-migration.md) - Driver サービスのマイグレーション
- [Driver Refactoring](docs/driver-refactoring.md) - Driver サービスのリファクタリング

## アーキテクチャ

### マイクロサービス構成
- 各サービスは独立したFlaskアプリとして動作
- APIはBlueprint単位で分割管理
- WebSocket（Flask-SocketIO）対応
- PostgreSQL + SQLAlchemy + Flask-Migrate によるDBマイグレーション

### インフラ構成
- nginx による HTTPS 強制 & リバースプロキシ
- 各サービスごとのアクセスログ
- メンテナンスページ対応
- 永続化（PostgreSQL / Redis / ログ / 証明書）

### セキュリティ
- HTTPS通信の強制
- LDAP認証（学生）
- ロールベースアクセス制御（RBAC）
- Redisベースのセッション管理
- **内部APIの保護** - マイクロサービス間APIを外部から隠蔽

## DBマイグレーション

各サービスで個別にマイグレーションを実行できます：

```bash
# studentサービスの例
docker-compose exec student flask db init        # 初回のみ
docker-compose exec student flask db migrate -m "Migration message"
docker-compose exec student flask db upgrade

# 同様に admin / driver でも実行可能
```

## ログ

- 各サービスの `/app/logs/access.log` にアクセスログを記録
- `docker-compose.yml` の `./logs` にマウントされ、ホスト側にも保存
- アクセス元IPアドレス、アクセスパス、タイムスタンプを記録

## トラブルシューティング

### 証明書エラーが発生した場合
```powershell
# Windows
.\generate_cert.ps1

# Mac/Linux
./generate_cert.sh
```

### コンテナが起動しない場合
```bash
# ログを確認
docker logs test-student-1
docker logs test-admin-1
docker logs test-driver-1

# 手動でコンテナ停止・削除
docker-compose down
docker system prune -f
```

### adminサービスのみ起動失敗する場合
まれに admin サービスのみ起動が失敗することがあります。その場合は再度起動コマンドを実行してください。

### データベースを完全にリセットしたい場合
```bash
# すべてのコンテナとボリュームを削除
docker-compose down -v

# 再起動
./start-dev.ps1 init  # Windows
./start-dev.sh init   # Mac/Linux
```

### 内部APIセキュリティのテスト
システムのセキュリティ設定が正しく動作しているか確認できます：
```powershell
# Windows
.\test-internal-api-security.ps1
```
詳細は [内部APIセキュリティガイド](docs/internal-api-security.md) を参照してください。

## ライセンス

このプロジェクトは内部使用を目的としています。

## 貢献

プロジェクトへの貢献に関する詳細は、開発チームにお問い合わせください。

## サポート

問題が発生した場合は、以下を確認してください：

1. [起動ガイド](docs/startup-guide.md)
2. [エラーハンドリングガイド](docs/error-handling.md)
3. 該当する機能別ガイド

それでも解決しない場合は、開発チームにお問い合わせください。
