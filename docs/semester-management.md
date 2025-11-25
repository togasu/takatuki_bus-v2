# 学期管理システム

本システムでは、日付ベースで学期を管理し、学期が変わった際に自動的にユーザーデータの移行を行います。

## 概要

### 学期テーブル (Semester)
- `id`: 学期ID
- `name`: 学期名（例：「2024年秋学期」）
- `start_date`: 学期開始日
- `end_date`: 学期終了日
- `is_active`: アクティブな学期かどうか
- `created_at`: 作成日時
- `updated_at`: 更新日時

### 学期切り替え履歴テーブル (SemesterTransition)
- `id`: 切り替えID
- `from_semester_id`: 切り替え前学期ID
- `to_semester_id`: 切り替え後学期ID
- `transition_date`: 切り替え実行日時
- `users_migrated`: 移行されたユーザー数
- `status`: 切り替え状況（completed, failed）
- `notes`: メモ

## セットアップ

### 1. データベースマイグレーション
```bash
cd student
python add_semester_tables.py
```

### 2. 初期学期データの確認
```bash
python semester_cli.py list
```

## 使用方法

### CLIコマンド

#### 学期一覧表示
```bash
python semester_cli.py list
```

#### 新しい学期を作成
```bash
python semester_cli.py create "2024年春学期" 2024-04-01 2024-08-31
python semester_cli.py create "2024年秋学期" 2024-09-01 2025-01-31 --active
```

#### 学期をアクティブにする
```bash
python semester_cli.py activate 2
```

#### 学期切り替え（ユーザー移行込み）
```bash
python semester_cli.py switch 2
```

#### 自動学期チェック・切り替え
```bash
python semester_cli.py auto-check
```

#### 現在の学期状況を確認
```bash
python semester_cli.py status
```

#### ユーザー移行のみ実行
```bash
python semester_cli.py migrate-users
```

### API エンドポイント

#### 学期一覧取得
```
GET /api/semester/list
```

#### アクティブな学期取得
```
GET /api/semester/active
```

#### 現在の日付に該当する学期取得
```
GET /api/semester/current
```

#### 学期作成
```
POST /api/semester/create
{
    "name": "2024年春学期",
    "start_date": "2024-04-01",
    "end_date": "2024-08-31",
    "is_active": false
}
```

#### 学期切り替え
```
POST /api/semester/switch
{
    "semester_id": 2,
    "migrate_users": true
}
```

#### 自動学期チェック
```
POST /api/semester/auto-check
```

## 学期切り替えプロセス

### 1. 手動切り替え
管理者が手動で学期を切り替える場合：

1. 新しい学期を作成（必要に応じて）
2. `switch` コマンドまたはAPIで学期切り替えを実行
3. 以下の処理が自動実行される：
   - 現在のUserテーブルのデータをLastSemester_userテーブルに移行
   - Userテーブルをクリア
   - 新しい学期をアクティブに設定
   - 切り替え履歴を記録

### 2. 自動切り替え
`auto-check` を実行すると：

1. 現在の日付が新しい学期の期間内かどうかをチェック
2. 該当する学期がある場合、自動的に切り替えを実行

### 3. 定期実行の設定
cronやタスクスケジューラーで定期的に自動チェックを実行：

```bash
# 毎日午前2時に自動チェック
0 2 * * * cd /path/to/student && python semester_cli.py auto-check
```

## 注意事項

### データの安全性
- 学期切り替えは**元に戻せない操作**です
- 切り替え前に必ずデータベースのバックアップを取ってください
- テスト環境で十分に動作確認を行ってください

### 学期期間の設定
- 学期期間は重複しないように設定してください
- 通常は以下のような期間設定を推奨：
  - 春学期：4月1日 - 8月31日
  - 秋学期：9月1日 - 1月31日

### パフォーマンス
- 大量のユーザーがいる場合、移行処理に時間がかかる可能性があります
- 本番環境では負荷の少ない時間帯に実行することを推奨します

## トラブルシューティング

### 学期切り替えが失敗した場合
1. ログを確認：
```bash
tail -f logs/student.log
```

2. 現在の状況確認：
```bash
python semester_cli.py status
```

3. データベースの整合性確認：
```python
# Pythonコンソールで実行
from app import create_app
from app.models import User, LastSemester_user, Semester

app = create_app()
with app.app_context():
    user_count = User.query.count()
    last_user_count = LastSemester_user.query.count()
    active_semester = Semester.query.filter_by(is_active=True).first()
    
    print(f"現在のユーザー数: {user_count}")
    print(f"前学期ユーザー数: {last_user_count}")
    print(f"アクティブ学期: {active_semester.name if active_semester else 'なし'}")
```

### よくある問題

#### Q: 「アクティブな学期がありません」エラー
A: 以下を確認してください：
1. 学期が作成されているか：`python semester_cli.py list`
2. いずれかの学期をアクティブにする：`python semester_cli.py activate <学期ID>`

#### Q: 学期期間が重複するエラー
A: 既存の学期の期間を確認し、重複しない期間で学期を作成してください。

#### Q: ユーザー移行後にデータが見つからない
A: `LastSemester_user` テーブルを確認してください。データは削除されずに移行されています。

## 開発者向け情報

### モデル構造
- `app/models/semester.py`: 学期関連のモデル定義
- `app/utils/semester_utils.py`: 学期管理のビジネスロジック
- `app/routes/semester_api.py`: API エンドポイント定義

### テスト
```bash
# 学期管理機能のテスト（今後実装予定）
python -m pytest tests/test_semester_management.py
```

### カスタマイズ
学期の自動切り替えロジックをカスタマイズする場合は、
`app/utils/semester_utils.py` の `auto_semester_check` メソッドを修正してください。