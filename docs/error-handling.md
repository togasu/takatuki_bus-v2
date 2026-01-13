# エラーハンドリング実装ガイド

## 概要
本プロジェクトの全サービス（admin、student、driver）に包括的なエラーハンドリングを実装しました。

## 実装内容

### 1. エラーハンドリングユーティリティ
各サービスの `app/utils/error_handlers.py` にて以下を実装：

- **ErrorLogger**: エラーログの統一記録
- **create_error_response**: 標準的なエラーレスポンス生成
- **専用エラーハンドラー**: データベース、Redis、認証、認可、バリデーション等のエラー処理
- **register_error_handlers**: Flaskアプリにエラーハンドラーを自動登録

### 2. 安全なルート実行デコレータ
各サービスの `app/utils/decorators.py` にて以下を実装：

- **@safe_route**: 一般的なルートエラーハンドリング
- **@safe_api_route**: APIルート専用の包括的エラーハンドリング（バリデーション・認証込み）
- **@validate_json_data**: JSONデータのバリデーション
- **@require_auth_token**: 認証トークンの必須チェック
- **@log_request**: リクエストログの記録

## エラーハンドリング対応範囲

### HTTPステータスコード
- 400: 不正なリクエスト
- 401: 認証エラー
- 403: 認可エラー
- 404: リソースが見つからない
- 405: 許可されていないメソッド
- 429: レート制限
- 500: 内部サーバーエラー
- 503: サービス利用不可

### データベースエラー
- **psycopg2.IntegrityError**: データ整合性エラー
- **psycopg2.OperationalError**: データベース接続エラー
- **その他psycopg2.Error**: 一般的なデータベースエラー

### セッション管理エラー
- **redis.RedisError**: Redisセッションサービスエラー

### バリデーションエラー
- **ValueError**: 値の妥当性エラー
- **KeyError**: 必須パラメータ不足
- **TypeError**: 型エラー

## 使用方法

### 1. APIルートでのエラーハンドリング

```python
from app.utils.decorators import safe_api_route

@bp.route("/api/users", methods=["POST"])
@safe_api_route(required_fields=["username", "email", "password"])
def create_user():
    data = request.get_json()
    # エラーハンドリングは自動的に適用される
    # ...
```

### 2. 一般ルートでのエラーハンドリング

```python
from app.utils.decorators import safe_route

@bp.route("/dashboard")
@safe_route
def dashboard():
    # エラーが発生した場合は自動的にハンドリングされる
    # ...
```

### 3. 手動エラーレスポンス

```python
from app.utils.error_handlers import create_error_response

def some_function():
    if error_condition:
        return create_error_response(
            "エラーメッセージ",
            400,
            "Error Type"
        )
```

## WebSocketエラーハンドリング

WebSocketイベントハンドラーにもエラーハンドリングを追加：

```python
@socketio.on("connect")
def handle_connect():
    try:
        # WebSocket接続処理
        pass
    except Exception as e:
        ErrorLogger.log_error(e)
        emit("error", {"message": "接続エラーが発生しました"})
```

## ログ出力

エラーは以下の情報と共にログに記録されます：
- エラーメッセージ
- HTTPメソッド
- URL
- IPアドレス
- ユーザーエージェント
- スタックトレース

## 設定

各サービスの `app/__init__.py` でエラーハンドラーを自動登録：

```python
from app.utils.error_handlers import register_error_handlers
register_error_handlers(app)
```

## 利点

1. **一貫性**: 全サービスで統一されたエラーハンドリング
2. **ログ記録**: 詳細なエラーログで問題の特定が容易
3. **ユーザビリティ**: 分かりやすいエラーメッセージ
4. **メンテナンス性**: デコレータによる簡単な適用
5. **スケーラビリティ**: 新しいエラータイプへの対応が容易

## 注意事項

- 本番環境では詳細なエラー情報を隠す設定を追加することを推奨
- ログレベルを適切に設定してパフォーマンスに影響しないよう注意
- セキュリティ上重要な情報がエラーメッセージに含まれないよう注意
