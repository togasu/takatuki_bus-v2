# Admin Service - 管理者向け管理システム

## 概要

Admin Serviceは、バスシステム全体を管理するための管理者向けWebアプリケーションです。学生管理、ドライバー管理、バス管理、ペナルティ管理、学期管理などの機能を提供します。

## 主な機能

### 1. 学生管理
- 学生一覧表示・検索
- 学生詳細情報の確認
- ペナルティの付与・解除
- 予約履歴の確認
- 学生データのエクスポート

### 2. ドライバー管理
- ドライバー登録・編集・削除
- ドライバー一覧表示
- 運行履歴の確認
- アカウント管理

### 3. バス管理
- バス情報の登録・編集・削除
- 運行スケジュール管理
- 座席管理
- リアルタイム予約状況確認

### 4. ペナルティ管理
- 手動ペナルティの付与
- ペナルティ理由の選択
- 解除時間の設定
- ペナルティ詳細の確認
- 自動ペナルティの管理

### 5. 学期管理
- 学期の作成・編集・削除
- 学期切り替え
- ユーザーデータの移行
- 自動学期チェック

### 6. 権限管理
- 3段階の権限レベル（Guest/Normal/Admin）
- ユーザーごとの権限設定
- ロールベースアクセス制御（RBAC）

## プロジェクト構造

```
admin/
├── app/
│   ├── __init__.py              # アプリケーションファクトリ
│   ├── auth.py                  # 認証機能
│   ├── authorization.py         # 認可機能（権限チェック）
│   ├── api_client.py            # Student Service APIクライアント
│   ├── database.py              # データベース設定
│   ├── models/                  # データモデル
│   │   ├── __init__.py
│   │   ├── user.py             # 管理者ユーザーモデル
│   │   └── permission.py       # 権限モデル
│   ├── routes/                  # ルーティング
│   │   ├── __init__.py
│   │   ├── auth.py             # 認証関連ルート
│   │   ├── dashboard.py        # ダッシュボード
│   │   ├── student_management.py  # 学生管理
│   │   ├── driver_management.py   # ドライバー管理
│   │   ├── bus_management.py      # バス管理
│   │   └── semester_management.py # 学期管理
│   ├── utils/                   # ユーティリティ
│   │   ├── __init__.py
│   │   ├── error_handlers.py   # エラーハンドリング
│   │   └── decorators.py       # デコレータ
│   ├── templates/               # HTMLテンプレート
│   └── static/                  # 静的ファイル
├── init_permissions.py          # 権限初期化スクリプト
├── create_test_admin.py         # テスト管理者作成
├── app_run.py                   # アプリケーション起動
├── requirements.txt             # 依存関係
├── uwsgi.ini                    # uWSGI設定
└── Dockerfile
```

## セットアップ

### 前提条件
- Python 3.7以上
- PostgreSQL
- Redis

### 1. データベースマイグレーション

```bash
cd admin
python init_migration.py
```

### 2. 権限の初期化

```bash
python init_permissions.py
```

### 3. テスト管理者の作成

```bash
python create_test_admin.py
```

## 権限システム

Admin Serviceは3段階の権限レベルを提供します：

### Guest権限
- **対象**: 外部の開発者
- **アクセス範囲**: Student ServiceのバスAPIと座席API（個人情報除く）のみ

### Normal権限
- **対象**: 一般管理者
- **アクセス範囲**: アカウント作成・削除以外のすべての操作
- **具体的な操作**:
  - 学生情報の閲覧・更新
  - ドライバー管理
  - バス管理
  - ペナルティ管理
  - 学期管理

### Admin権限
- **対象**: システム管理者
- **アクセス範囲**: すべての操作が可能
- **具体的な操作**:
  - アカウントの作成・削除
  - 権限の変更
  - システム全体の管理

詳細は [権限システムガイド](permissions-system.md) を参照してください。

## API クライアント

Admin ServiceはStudent Serviceと連携してデータを取得・操作します。

### 主なAPIエンドポイント

```python
# 学生一覧取得
GET /api/management/students

# ペナルティ付与
POST /api/management/apply_penalty
{
    "student_id": "k123456",
    "reason": "未乗車（無断欠席）",
    "end_time": "2024-12-31 22:00:00"
}

# ペナルティ解除
POST /api/management/clear_penalty
{
    "student_id": "k123456"
}

# 学期切り替え
POST /api/semester/switch
{
    "semester_id": 2,
    "migrate_users": true
}
```

## エラーハンドリング

Admin Serviceには包括的なエラーハンドリングが実装されています：

- データベースエラー
- API通信エラー
- 認証・認可エラー
- バリデーションエラー

詳細は [エラーハンドリングガイド](error-handling.md) を参照してください。

## デコレータ

### 権限チェック

```python
from app.authorization import require_permission, require_role

@app.route("/api/users", methods=["POST"])
@require_permission("admin_user", "create")
def create_user():
    # adminロールのみアクセス可能
    pass
```

### エラーハンドリング

```python
from app.utils.decorators import safe_api_route

@app.route("/api/data", methods=["GET"])
@safe_api_route
def get_data():
    # エラーは自動的にハンドリングされる
    pass
```

## マイグレーション

### 自動マイグレーション

コンテナ起動時に自動的にマイグレーションが実行されます。

### 手動マイグレーション

```bash
# コンテナ内で実行
docker exec -it takatuki_bus-v2-admin-1 bash
python init_migration.py
```

詳細は [Admin Migration Guide](admin-migration.md) を参照してください。

## テスト

### テストアカウント作成

```bash
python create_test_admin.py
```

デフォルトのテストアカウント:
- **ユーザー名**: admin_test
- **パスワード**: admin123
- **権限**: admin

## トラブルシューティング

### よくある問題

#### Q: 起動時にマイグレーションエラーが発生する
A: 以下を試してください：
```bash
docker exec -it takatuki_bus-v2-admin-1 python init_migration.py
```

#### Q: Student Serviceとの通信エラー
A: 両方のサービスが起動していることを確認してください：
```bash
docker ps | grep -E 'admin|student'
```

#### Q: 権限エラーが発生する
A: 権限が正しく初期化されているか確認：
```bash
docker exec -it takatuki_bus-v2-admin-1 python init_permissions.py
```

## セキュリティ

- すべてのパスワードはハッシュ化して保存
- セッション管理にRedisを使用
- HTTPS通信の強制
- ロールベースアクセス制御（RBAC）
- CSRFトークンによる保護

## パフォーマンス

- データベースクエリの最適化
- Redisによるセッションキャッシング
- 非同期通信の活用
- ページネーション実装

## 今後の拡張

- 統計・分析機能
- メール通知機能
- ログのエクスポート機能
- APIドキュメント自動生成
- モバイル対応

## 関連ドキュメント

- [権限システム](permissions-system.md)
- [Admin Migration Guide](admin-migration.md)
- [エラーハンドリング](error-handling.md)
- [ペナルティシステム](penalty-system.md)
- [学期管理システム](semester-management.md)
