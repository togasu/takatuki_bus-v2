# ドライバーシステム リファクタリング（Redis + Student Service統合版）

このドキュメントは、main.pyのリファクタリング後のドライバーシステムの構造について説明します。

## リファクタリングの目的

従来の巨大なmain.pyファイル（700行以上）を、保守性と可読性を向上させるために機能別に分離し、適切な設計パターンを適用しました。また、以下の改善を実施しました：

- **Hashテーブル → Redis**: セッション管理をRedisベースに変更
- **Bus/Seat/Reservation → Student Service**: Student serviceのモデルを利用

## 新しいディレクトリ構造

```
driver/app/
├── main.py                     # エントリーポイント（簡素化）
├── driver_initializer.py       # アプリケーション初期化とファクトリー関数
├── database.py                 # データベース設定
├── auth.py                     # 認証関連機能
│
├── models/                     # データベースモデル
│   ├── __init__.py
│   └── driver.py               # Driver, QA（Bus系はStudent serviceから参照）
│
├── routes/                     # ルーティング
│   ├── __init__.py
│   ├── main_routes.py          # メイン、ログイン、バス関連
│   ├── yoyaku_routes.py        # 予約関連
│   ├── question_routes.py      # 質問、Q&A、メール関連
│   └── other_routes.py         # その他（tips等）
│
├── services/                   # ビジネスロジック
│   ├── __init__.py
│   └── business_logic.py       # BusService, SeatService, DriverService, QAService
│
├── utils/                      # ユーティリティ
│   ├── __init__.py
│   ├── helper_functions.py     # 汎用ヘルパー関数（Redis対応）
│   ├── redis_manager.py        # Redis管理クラス ✨新規
│   ├── student_api_client.py   # Student Service APIクライアント ✨新規
│   ├── auth_utils.py          # 認証ユーティリティ
│   ├── error_handlers.py      # エラーハンドリング
│   └── (その他既存ユーティリティ)
│
├── static/                     # 静的ファイル
├── templates/                  # テンプレート
└── ...
```

## 主な変更点

### 1. Redis によるセッション管理 ✨新機能

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

### 2. Student Service との統合 ✨新機能

Bus、Seat、Reservationモデルは Student service のものを参照：

```python
# Student serviceのAPIクライアント経由でデータアクセス
from app.utils.student_api_client import get_student_client

client = get_student_client()
buses = client.get_buses_by_number_and_time(bus_number, limit=5)
```

### 3. モデルの最適化

- **Driver**: ドライバー情報（そのまま）
- **QA**: Q&A情報（そのまま）
- **Hash**: 削除（Redis使用）
- **Bus/Seat/Reservation**: Student service参照

### 4. 設定の改善

```python
# Redis設定
app.config['REDIS_HOST'] = 'localhost'
app.config['REDIS_PORT'] = 6379
app.config['REDIS_DB'] = 1

# Student service のDB参照
app.config['SQLALCHEMY_BINDS'] = {
    'db3': 'sqlite:///../../student/instance/yoyaku_seki.db'
}
```

## 必要な依存関係

### 新規依存関係
```bash
pip install redis
pip install requests
```

### Redis サーバー

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Docker
docker run -d -p 6379:6379 redis:latest
```

## 使用方法

### 新しい方法（推奨）
```python
from app.driver_initializer import create_driver_app

app = create_driver_app()
app.run(debug=True, port=8080)
```

### 従来の方法（互換性保持）
```python
from app.main import driver

app = driver()
app.run(debug=True, port=8080)
```

## 設定

### Redis 設定
```python
# 環境変数または設定ファイルで指定可能
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
```

### Student Service 連携
```python
STUDENT_SERVICE_URL=http://localhost:5000
```

## 利点

1. **パフォーマンス向上**: Redisによる高速セッション管理
2. **スケーラビリティ**: マイクロサービス間の疎結合
3. **保守性の向上**: 機能ごとに分離されたファイル構造
4. **データ整合性**: Student serviceとの統一されたデータモデル
5. **拡張性**: 新機能の追加が容易

## 互換性

- 既存の`driver()`関数は保持され、既存のコードとの互換性を維持
- 全ての既存の機能は新しい構造でも正常に動作
- Redis/Student service が利用できない場合のフォールバック機能

## 今後の改善予定

1. Student Service との完全なAPI統合
2. Redis クラスター対応
3. より詳細なエラーハンドリング
4. ユニットテストの追加
5. パフォーマンス監視機能

---

このリファクタリングにより、ドライバーシステムはよりモダンで拡張性の高いアーキテクチャになりました。