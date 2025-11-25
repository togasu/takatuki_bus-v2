# Driver Service - ドライバー向け運行管理システム

## 概要

Driver Serviceは、バス運転手向けの運行管理Webアプリケーションです。予約確認、承認、Q&A機能などを提供します。

## 主な機能

### 1. 予約管理
- リアルタイム予約状況の確認
- 予約の承認・却下
- 座席別予約者の確認
- 予約履歴の閲覧

### 2. バス運行管理
- 担当バスの確認
- 運行スケジュール管理
- 乗車確認機能
- 運行履歴の記録

### 3. Q&A機能
- 学生からの質問受付
- 質問への回答
- Q&A履歴の管理
- カテゴリ別質問管理

### 4. メール機能
- 予約確認メール送信
- 運行情報の通知
- 緊急連絡機能

### 5. Tips機能
- 運行時の注意事項
- よくある質問
- マニュアル・ガイド

## プロジェクト構造

```
driver/
├── app/
│   ├── main.py                  # エントリーポイント
│   ├── driver_initializer.py   # アプリケーション初期化
│   ├── database.py              # データベース設定
│   ├── auth.py                  # 認証機能
│   ├── models/                  # データモデル
│   │   ├── __init__.py
│   │   ├── driver.py           # ドライバーモデル
│   │   └── qa.py               # Q&Aモデル
│   ├── routes/                  # ルーティング
│   │   ├── __init__.py
│   │   ├── main_routes.py      # メイン・ログイン・バス関連
│   │   ├── yoyaku_routes.py    # 予約関連
│   │   ├── question_routes.py  # 質問・Q&A・メール関連
│   │   └── other_routes.py     # その他（tips等）
│   ├── services/                # ビジネスロジック
│   │   ├── __init__.py
│   │   └── business_logic.py   # 各種サービスクラス
│   ├── utils/                   # ユーティリティ
│   │   ├── __init__.py
│   │   ├── helper_functions.py # 汎用ヘルパー関数
│   │   ├── redis_manager.py    # Redis管理クラス
│   │   ├── student_api_client.py # Student Service APIクライアント
│   │   ├── auth_utils.py       # 認証ユーティリティ
│   │   └── error_handlers.py   # エラーハンドリング
│   ├── templates/               # HTMLテンプレート
│   └── static/                  # 静的ファイル
├── create_test_driver.py        # テストドライバー作成
├── app_run.py                   # アプリケーション起動
├── requirements.txt             # 依存関係
├── uwsgi.ini                    # uWSGI設定
└── Dockerfile
```

## リファクタリング

従来の巨大なmain.pyファイル（700行以上）を機能別に分離し、保守性と可読性を向上させました。

### 主な改善点

#### 1. Redisによるセッション管理
従来のSQLiteベースのHashテーブルから、Redisベースのセッション管理に変更：

```python
from app.utils.redis_manager import get_redis_manager

# ハッシュ生成
redis_manager = get_redis_manager()
hashed_num = redis_manager.generate_hash_login(username)

# ハッシュ検証
username = redis_manager.check_hash(hashed_num)
```

**利点:**
- 高速なセッション管理
- 自動的な期限切れ機能
- スケーラビリティの向上

#### 2. Student Serviceとの統合
Bus、Seat、Reservationモデルは Student Serviceのものを参照：

```python
# Student ServiceのAPIクライアント経由でデータアクセス
from app.utils.student_api_client import get_student_client

client = get_student_client()
buses = client.get_buses_by_number_and_time(bus_number, limit=5)
```

#### 3. モデルの最適化
- **Driver**: ドライバー情報（そのまま）
- **QA**: Q&A情報（そのまま）
- **Hash**: 削除（Redis使用）
- **Bus/Seat/Reservation**: Student Service参照

詳細は [Driver Refactoring](driver-refactoring.md) を参照してください。

## セットアップ

### 前提条件
- Python 3.7以上
- PostgreSQL
- Redis
- Student Serviceが起動していること

### 1. データベースマイグレーション

```bash
cd driver
python init_migration.py
```

### 2. テストドライバーの作成

```bash
python create_test_driver.py
```

## 認証とセッション管理

### Redisベースのセッション

Driver Serviceでは、Redisを使用してセッション管理を行います：

```python
# Redis設定
app.config['REDIS_HOST'] = 'redis'
app.config['REDIS_PORT'] = 6379
app.config['REDIS_DB'] = 1
```

### 認証フロー

1. ドライバーがログイン
2. Redisでハッシュ化されたセッションIDを生成
3. セッションIDをCookieに保存
4. 各リクエストでセッションIDを検証

## Student Service連携

Driver ServiceはStudent Serviceと連携してバス・座席・予約データを取得します。

### APIクライアント使用例

```python
from app.utils.student_api_client import get_student_client

client = get_student_client()

# バス情報取得
buses = client.get_buses_by_number_and_time(bus_number="1", limit=5)

# 座席情報取得
seats = client.get_seats_by_bus_id(bus_id=1)

# 予約情報取得
reservations = client.get_reservations_by_bus_id(bus_id=1)
```

## ビジネスロジック

### サービスクラス

Driver Serviceは以下のサービスクラスを提供します：

#### BusService
- バス情報の取得
- 運行スケジュール管理

#### SeatService
- 座席情報の取得
- 座席状態の管理

#### DriverService
- ドライバー情報の管理
- 認証・認可

#### QAService
- 質問の管理
- 回答の記録

```python
from app.services.business_logic import BusService, QAService

# バス情報取得
bus_service = BusService()
buses = bus_service.get_available_buses()

# Q&A管理
qa_service = QAService()
questions = qa_service.get_unanswered_questions()
```

## エラーハンドリング

Driver Serviceには包括的なエラーハンドリングが実装されています：

```python
from app.utils.decorators import safe_route

@app.route("/dashboard")
@safe_route
def dashboard():
    # エラーは自動的にハンドリングされる
    pass
```

詳細は [エラーハンドリングガイド](error-handling.md) を参照してください。

## マイグレーション

### 自動マイグレーション

コンテナ起動時に自動的にマイグレーションが実行されます。

### 手動マイグレーション

```bash
# コンテナ内で実行
docker exec -it takatuki_bus-v2-driver-1 bash
python init_migration.py
```

### マイグレーションのスキップ

```bash
# 環境変数で制御
SKIP_MIGRATION=true docker-compose up driver
```

詳細は [Driver Migration Guide](driver-migration.md) を参照してください。

## テスト

### テストドライバー作成

```bash
docker exec -it takatuki_bus-v2-driver-1 python create_test_driver.py
```

デフォルトのテストアカウント:
- **ユーザー名**: driver_test
- **パスワード**: driver123

## 主な画面

### 1. ダッシュボード
- 本日の運行予定
- 未承認の予約一覧
- 未回答の質問数

### 2. 予約管理画面
- バス別予約一覧
- 座席別予約状況
- 予約の承認・却下

### 3. Q&A管理画面
- 質問一覧
- 回答入力
- Q&A履歴

### 4. 運行履歴画面
- 過去の運行記録
- 乗車人数統計
- 運行レポート

## 設定

### Redis設定

```python
app.config['REDIS_HOST'] = 'redis'
app.config['REDIS_PORT'] = 6379
app.config['REDIS_DB'] = 1  # Driver Service専用DB
```

### Student Service連携設定

```python
app.config['STUDENT_API_BASE_URL'] = 'http://student:8000'
```

### データベース設定

```python
# Driver Service専用DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@postgres/mydb'

# Student ServiceのDBへの参照
app.config['SQLALCHEMY_BINDS'] = {
    'student': 'postgresql://user:pass@postgres/mydb'
}
```

## トラブルシューティング

### よくある問題

#### Q: Student Serviceとの通信エラー
A: 両方のサービスが起動していることを確認：
```bash
docker ps | grep -E 'driver|student'
```

#### Q: Redis接続エラー
A: Redisコンテナが起動しているか確認：
```bash
docker ps | grep redis
```

#### Q: セッションが保持されない
A: Redis内のセッションデータを確認：
```bash
docker exec -it takatuki_bus-v2-redis-1 redis-cli
SELECT 1
KEYS *
```

#### Q: マイグレーションエラー
A: 手動でマイグレーションを実行：
```bash
docker exec -it takatuki_bus-v2-driver-1 python init_migration.py
```

## セキュリティ

- パスワードのハッシュ化保存
- Redisベースのセッション管理
- HTTPS通信の強制
- CSRF保護
- セッションの自動期限切れ

## パフォーマンス

- Redisによる高速セッション管理
- Student Service APIのキャッシング
- データベースクエリの最適化
- 非同期処理の活用

## 今後の拡張

- モバイルアプリ対応
- プッシュ通知機能
- 運行統計のグラフ化
- 自動レポート生成
- GPS連携機能

## 関連ドキュメント

- [Driver Refactoring](driver-refactoring.md)
- [Driver Migration Guide](driver-migration.md)
- [エラーハンドリング](error-handling.md)
- [Student Service](student-service.md)
