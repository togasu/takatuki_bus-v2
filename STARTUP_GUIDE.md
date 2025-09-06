# バスシステム開発環境 起動スクリプト

## 概要

このスクリプトは、バスシステム開発環境を簡単に起動するためのツールです。証明書の管理、Dockerコンテナの管理、データベースの初期化を自動で行います。

## 使用方法

### PowerShell（Windows）

```powershell
# 通常起動（既存のデータベースを保持）
./start-dev.ps1

# データベース初期化して起動
./start-dev.ps1 init
```

### Bash（Linux/macOS/WSL）

```bash
# 通常起動（既存のデータベースを保持）
./start-dev.sh

# データベース初期化して起動
./start-dev.sh init
```

## 実行内容

スクリプトは以下の処理を順番に実行します：

### Step 1: 証明書の確認と作成
- `certs/server.crt` と `certs/server.key` の存在を確認
- 証明書が存在しない場合は `generate_cert.ps1` または `generate_cert.sh` を実行して新規作成

### Step 2: 既存Dockerコンテナの停止
- `test-` プレフィックスを持つコンテナを `docker-compose down` で停止
- データベースボリュームは保持される（`init` オプション未指定時）

### Step 3: データベース初期化判定
- `init` オプションが指定された場合：データベースボリューム (`test_postgres_data`) を削除
- 未指定の場合：既存のデータベースを保持

### Step 4: Dockerコンテナの起動
- `docker-compose up --build -d` でコンテナを再ビルド・起動

### Step 5: コンテナ起動待機
- 全てのコンテナ（nginx, student, admin, driver, postgres, redis）の起動を確認
- 最大30回リトライ（約60秒）

### Step 6: データベース初期化（initオプション時のみ）
- 各サービス（admin, student, driver）の `init_migration.py` を実行
- データベーステーブルの作成とマイグレーション

### Step 7: システム起動確認
- `https://localhost` への接続テスト
- HTTPSレスポンスの確認

## システム構成

起動後、以下のサービスが利用可能になります：

- **🌐 メインシステム**: https://localhost
- **🔧 管理画面**: https://localhost/admin
- **🚛 ドライバー画面**: https://localhost/driver

## 認証方法

### 学生ユーザー
- **ユーザー名**: k番号（例: k123456）
- **認証方式**: LDAP認証
- **注意**: k番号で始まるユーザー名のみ受け付けます

### 管理者・ドライバー
- 各サービス独自の認証システムを使用

## トラブルシューティング

### 証明書エラーが発生した場合
```powershell
# 証明書を手動で再生成
./generate_cert.ps1  # Windows
./generate_cert.sh   # Linux/macOS
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

### データベースを完全にリセットしたい場合
```bash
# 全てのボリュームを削除（注意：データは完全に失われます）
docker-compose down -v
./start-dev.ps1 init  # または ./start-dev.sh init
```

## 停止方法

```bash
# システム停止（データベースは保持）
docker-compose down

# システム停止＋ボリューム削除（データベースも削除）
docker-compose down -v
```

## 開発時の便利なコマンド

```bash
# 特定のサービスのみ再ビルド
docker-compose up --build -d student

# ログのリアルタイム監視
docker logs -f test-student-1

# データベース直接接続
docker exec -it test-postgres-1 psql -U user -d mydb

# コンテナ内でのコマンド実行
docker exec -it test-student-1 bash
```
