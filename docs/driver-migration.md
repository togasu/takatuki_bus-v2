# Driver Service Migration Guide

## 起動方法

### 1. start-dev.ps1 での起動（推奨）
```powershell
# 通常起動（既存データ保持）
./start-dev.ps1

# データベース初期化して起動
./start-dev.ps1 init

# データベース初期化 + テストデータ作成
./start-dev.ps1 init debug
```

### 2. driverサービス単体での起動
```bash
# マイグレーションありで起動
docker-compose up driver

# マイグレーションなしで起動（既存のDBを使用）
SKIP_MIGRATION=true docker-compose up driver

# 開発環境として起動
ENVIRONMENT=development docker-compose up driver
```

### 3. マイグレーションエラーが発生した場合
```bash
# 1. コンテナーに入る
docker exec -it takatuki_bus-v2-driver-1 bash

# 2. マイグレーション状態を確認
flask db current

# 3. マイグレーション履歴を確認
flask db history

# 4. 手動でマイグレーション初期化
python init_migration.py

# 5. 特定のリビジョンにスタンプ（必要に応じて）
flask db stamp head
```

## マイグレーション戦略

### 新規環境
- マイグレーションディレクトリがない場合は自動で初期化
- 新しいマイグレーションファイルを作成して適用

### 既存環境
- 既存のマイグレーション履歴を尊重
- エラーが発生した場合は自動修復を試行
- 修復できない場合はベースライン作成

### 履歴不整合時の対処
1. Alembicバージョンテーブルをクリア
2. マイグレーションディレクトリを再作成
3. 既存スキーマからベースラインマイグレーション作成
4. ベースラインとしてマーク（実際の変更は適用しない）

## 環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| SKIP_MIGRATION | false | trueにするとマイグレーション処理をスキップ |
| ENVIRONMENT | development | 実行環境の指定 |
| POSTGRES_HOST | postgres | PostgreSQLホスト |
| POSTGRES_DB | mydb | データベース名 |
| POSTGRES_USER | user | データベースユーザー |
| POSTGRES_PASSWORD | pass | データベースパスワード |

## トラブルシューティング

### Q: "Can't locate revision identified by 'XXXXXX'" エラー
A: マイグレーション履歴の不整合です。以下を試してください：
1. `SKIP_MIGRATION=true` で起動
2. コンテナー内で `python init_migration.py` を実行
3. 必要に応じて `flask db stamp head` でマーク

### Q: start-dev.ps1 と単体起動で動作が異なる
A: start-dev.ps1は毎回クリーンなマイグレーションを実行します。
単体起動では既存の状態を保持するため、挙動が異なる場合があります。

### Q: データベースが見つからないエラー
A: PostgreSQLコンテナーが起動していることを確認してください：
```bash
docker-compose up postgres -d
```

## Driver固有の機能

### テストドライバーの作成
```bash
# driverコンテナー内でテストドライバーを作成
docker exec -it takatuki_bus-v2-driver-1 python create_test_driver.py
```

### ドライバー認証システムの確認
Driverサービスは独自の認証システムを持っています：
- ドライバー専用のログインシステム
- バス運行管理機能
- 乗客管理機能

### 開発時の注意点
- Driverサービスはadmin/studentサービスとは独立したデータベーステーブルを使用
- ドライバー情報は他のサービスとは分離されています
- バス運行データは実時間で更新されます