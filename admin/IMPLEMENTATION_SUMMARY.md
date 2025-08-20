# 権限システム実装完了報告

## 実装概要

要件に基づいて、以下の3つの権限レベルを持つ権限システムを実装しました：

### 権限レベル

1. **Guest権限**
   - 対象: 外部の開発者
   - アクセス範囲: studentのbusとseat（予約者名を除く）の個人情報を含まない情報のAPIのみ
   - 具体的権限: `student_bus:read`, `student_seat:read`

2. **Normal権限**
   - 対象: 一般的な管理者
   - アクセス範囲: アカウント作成・削除以外のすべての操作
   - 制限: `admin_user:create`, `admin_user:delete` は不可

3. **Admin権限**
   - 対象: システム管理者
   - アクセス範囲: すべての操作が可能

## 実装ファイル

### 1. 認可機能 (`app/authorization.py`)
- `require_permission(resource, action)`: 権限チェックデコレータ
- `require_role(allowed_roles)`: ロールチェックデコレータ
- `has_permission(user, resource, action)`: 権限判定ロジック
- `get_user_permissions(user)`: ユーザー権限一覧取得

### 2. Userモデル拡張 (`app/models/user.py`)
- 既存のroleフィールドを3つの権限レベル（guest, normal, admin）に対応
- 権限チェック用メソッドを追加:
  - `has_permission(resource, action)`
  - `get_permissions()`
  - `is_guest()`, `is_normal()`, `is_admin()`
- API エンドポイントに権限チェックを適用:
  - `GET /api/users` - normal, admin のみ
  - `POST /api/users` - admin のみ
  - `PUT /api/users/<id>` - normal, admin のみ
  - `DELETE /api/users/<id>` - admin のみ

### 3. Permissionモデル拡張 (`app/models/permission.py`)
- API エンドポイントに権限チェックを適用:
  - `GET /api/permissions` - normal, admin のみ
  - `POST /api/permissions` - normal, admin のみ

### 4. 権限初期化スクリプト (`init_permissions.py`)
- 定義された権限を自動的にデータベースに作成
- 各ロールの権限マッピングを定義

### 5. 認証機能拡張 (`app/auth.py`)
- `get_current_user()` 関数を追加

## テストファイル

### 1. ロジックテスト (`test_permission_logic.py`)
- 権限チェックロジックの単体テスト
- 16個のテストケースをすべて合格

### 2. APIデモ (`api_permission_demo.py`)
- 実際のFlask APIでの権限システム使用例
- モックトークンを使用したテスト用サーバー

## 使用方法

### セットアップ
1. 必要なパッケージをインストール: `pip install flask flask-sqlalchemy flask-migrate`
2. 権限を初期化: `python init_permissions.py`

### APIでの使用例
```python
@app.route("/api/endpoint", methods=["GET"])
@require_permission("resource_name", "action_name")
def my_endpoint():
    # このエンドポイントは指定された権限を持つユーザーのみアクセス可能
    pass

@app.route("/api/endpoint", methods=["POST"])
@require_role(["normal", "admin"])
def another_endpoint():
    # このエンドポイントはnormalまたはadminロールのユーザーのみアクセス可能
    pass
```

### ユーザーの権限確認
```python
user = get_current_user()
if user.has_permission("student_bus", "read"):
    # バス情報へのアクセス権限あり
    pass
```

## セキュリティ実装

- すべての機密APIエンドポイントに適切な権限チェックを適用
- ロールベースアクセス制御（RBAC）を実装
- 最小権限の原則に従い、各ロールに必要最小限の権限のみ付与
- 権限不足時には適切なHTTPステータスコード（403 Forbidden）を返す

## テスト結果

✅ **権限ロジックテスト: 16/16 合格**
- Guest権限: student_busとstudent_seatの読み取りのみ許可
- Normal権限: アカウント作成・削除以外すべて許可
- Admin権限: すべての操作許可

## 今後の拡張

- JWTトークンベースの認証機能
- より細かいリソース別権限設定
- 権限の動的割り当て機能
- 監査ログ機能

この実装により、要件通りの3段階権限システムが完成し、セキュアなAPIアクセス制御が可能になりました。
