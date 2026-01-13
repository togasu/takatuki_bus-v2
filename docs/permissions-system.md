# 権限システム使用ガイド

## 概要

このシステムでは、3つの権限レベルを定義しています：

### 1. Guest権限
- **対象**: 外部の開発者
- **アクセス可能範囲**: studentのbusとseat（予約者名を除く）の個人情報を含まない情報のAPIのみ
- **具体的な権限**:
  - `student_bus:read` - バス情報の読み取り（個人情報除く）
  - `student_seat:read` - 座席情報の読み取り（予約者名除く）

### 2. Normal権限
- **対象**: 一般的な管理者アカウント
- **アクセス可能範囲**: アカウント作成・削除以外のすべての操作
- **具体的な権限**:
  - ユーザー情報の読み取り・更新
  - 権限管理の全操作
  - ドライバー管理の全操作
  - 学生情報の全操作
  - バス・座席・コース・シーズン情報の全操作

### 3. Admin権限
- **対象**: システム管理者
- **アクセス可能範囲**: すべての操作が可能
- **具体的な権限**:
  - すべてのリソースに対する全操作
  - アカウントの作成・削除

## セットアップ

### 1. 権限の初期化

```bash
cd admin
python init_permissions.py
```

### 2. テストの実行

```bash
cd admin
python test_permissions.py
```

## API使用例

### 権限チェック付きのエンドポイント例

```python
from app.authorization import require_permission, require_role

@app.route("/api/users", methods=["GET"])
@require_permission("admin_user", "read")
def get_users():
    # normalまたはadminロールのユーザーのみアクセス可能
    pass

@app.route("/api/users", methods=["POST"])
@require_permission("admin_user", "create")
def create_user():
    # adminロールのユーザーのみアクセス可能
    pass

@app.route("/api/guest-data", methods=["GET"])
@require_role(["guest", "normal", "admin"])
def get_guest_data():
    # すべてのロールがアクセス可能
    pass
```

### ユーザーの権限確認

```python
# 現在のユーザーの権限を取得
user = get_current_user()
permissions = user.get_permissions()

# 特定の権限をチェック
if user.has_permission("student_bus", "read"):
    # バス情報を読み取り可能
    pass

# ロールチェック
if user.is_admin():
    # 管理者権限
    pass
elif user.is_normal():
    # 一般権限
    pass
elif user.is_guest():
    # ゲスト権限
    pass
```

## エラーレスポンス

権限不足の場合、以下のエラーレスポンスが返されます：

```json
{
    "error": "Insufficient permissions"
}
```

認証が必要な場合：

```json
{
    "error": "Authentication required"
}
```

ロール不足の場合：

```json
{
    "error": "Insufficient role"
}
```

## 権限の拡張

新しい権限を追加する場合は、以下の手順を実行してください：

1. `init_permissions.py`に新しい権限定義を追加
2. `authorization.py`の権限チェック関数を更新
3. 必要に応じてAPIエンドポイントにデコレータを追加

## セキュリティ注意事項

- すべての機密性の高いAPIエンドポイントには適切な権限チェックを追加してください
- パスワードは必ずハッシュ化して保存してください
- 権限の変更は慎重に行い、テストを実施してください
