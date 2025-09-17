# Student Service - Bus Reservation System

このディレクトリには学生向けのバス予約システムが含まれています。

## プロジェクト構造

```
student/
├── app/
│   ├── __init__.py          # アプリケーションファクトリ
│   ├── config.py            # 設定ファイル
│   ├── database.py          # データベース設定
│   ├── models/              # データモデル
│   │   ├── __init__.py
│   │   ├── bus.py          # バスモデル
│   │   ├── seat.py         # 座席モデル
│   │   ├── reservation.py  # 予約モデル
│   │   ├── user.py         # ユーザーモデル
│   │   ├── admin.py        # 管理者モデル
│   │   ├── token.py        # トークンモデル
│   │   └── cancel.py       # キャンセルモデル
│   ├── routes/              # ルーティング
│   │   ├── __init__.py
│   │   ├── auth.py         # 認証関連
│   │   ├── main.py         # メインページ
│   │   ├── booking.py      # 予約関連
│   │   └── cancel.py       # キャンセル関連
│   ├── utils/               # ユーティリティ
│   │   ├── __init__.py
│   │   ├── auth_utils.py   # 認証ユーティリティ
│   │   ├── datetime_utils.py # 日時ユーティリティ
│   │   └── bus_utils.py    # バスユーティリティ
│   └── templates/           # HTMLテンプレート
├── app_run.py               # アプリケーション起動ファイル
├── requirements.txt         # 依存関係
├── uwsgi.ini               # uWSGI設定
└── README.md               # このファイル
```

## 主な変更点

### 1. モデルの分離
- `yoyaku.py`の全モデルクラスを`models/`ディレクトリに分離
- 各モデルを個別ファイルに配置し、責任を明確化

### 2. ルーティングの分離
- 認証、メイン、予約、キャンセル機能をそれぞれ別のBlueprintに分離
- 機能別にファイルを分割し、保守性を向上

### 3. ユーティリティの分離
- LDAP認証、日時処理、バス管理機能を`utils/`に分離
- 再利用可能な関数として整理

### 4. トークン管理のRedis化
- データベースベースからRedisベースのセッション管理に変更
- 自動期限切れ機能によりメンテナンスが不要
- 高速なセッション検証
- スケーラブルなセッション管理

### 6. 動的モデルインポート機能
- `models/`ディレクトリに新しい`.py`ファイルを追加すると自動でインポート
- 手動で`__init__.py`を編集する必要がなくなる
- 新しいモデル作成用のヘルパー関数を提供

#### 新しいモデルの追加方法：

1. **手動作成**:
```python
# models/new_model.py
from .bus import db

class NewModel(db.Model):
    __tablename__ = "new_model"
    id = db.Column(db.Integer, primary_key=True)
    # 他のフィールドを追加
```

2. **ヘルパー使用**:
```bash
cd student/app/models
python model_helper.py NewModel new_table_name
```

3. **動作確認**:
```bash
cd student
python test_dynamic_models.py
```

### 7. Admin機能の分離
- admin関連の機能をadminサービスに移行
- studentサービスは学生のバス予約機能のみに特化
- Flask-Loginなど不要な依存関係を削除
- ログイン処理は学生（k番号）のみに対応

## セットアップ

### 前提条件
- Python 3.7以上
- Redis サーバー

### Redis のインストールと起動

#### Windows:
1. Redis for Windows をダウンロード
2. または Docker を使用: `docker run -d -p 6379:6379 redis:alpine`

#### Linux/Mac:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS (Homebrew)
brew install redis

# 起動
redis-server
```

### アプリケーションのセットアップ

1. 依存関係のインストール:
```bash
pip install -r requirements.txt
```

2. Redis サーバーの起動（別ターミナル）:
```bash
redis-server
```

3. アプリケーションの起動:
```bash
python app_run.py
```

## 注意事項

- 元の`yoyaku.py`の機能をできる限り保持しています
- データベース設定は環境に応じて調整が必要です
- テンプレートファイルは既存のものを使用する前提です
- ログファイルや設定ファイルのパスも適切に設定してください

## 今後の改善点

- エラーハンドリングの強化
- ログ機能の改善
- テストコードの追加
- セキュリティの強化
- パフォーマンスの最適化
