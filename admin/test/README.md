# Admin Test Directory

このディレクトリには管理者システムのテスト関連ファイルが含まれています。

## ファイル一覧

### データベース・ユーザー作成関連
- **`setup_db.py`**: データベースのテーブル作成とテストユーザー作成の統合スクリプト
- **`create_test_users.py`**: Flaskアプリ経由でテストユーザーを作成（循環インポート問題あり）
- **`create_test_users_sql.py`**: 直接SQLでテストユーザーを作成

### 認証テスト
- **`test_login_direct.py`**: データベース直接アクセスでログイン認証をテスト
- **`test_auth_api.py`**: HTTP API経由での認証テスト（requests必要）

### 権限システムテスト
- **`test_permissions.py`**: 権限システムの基本テスト
- **`test_permission_logic.py`**: 権限ロジックの詳細テスト
- **`simple_test_permissions.py`**: シンプルな権限テスト

## 現在の状況（2025年8月19日）

### ✅ 正常に動作する認証方法

1. **Admin API直接アクセス** - 完全に動作
   ```bash
   # ログイン
   curl -k -X POST "https://localhost/admin/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username":"admin_test","password":"admin123"}'
   
   # レスポンス例:
   # {"role":"admin","token":"xxx...","user_id":1,"username":"admin_test"}
   
   # 認証が必要なAPIアクセス
   curl -k -X GET "https://localhost/admin/api/users" \
     -H "X-Service-Auth: [取得したトークン]"
   ```

### ❌ 問題がある認証方法

1. **Student統合ログインページ** - 500エラー発生
   - URL: `https://localhost/auth`
   - 問題: Student側のテーブルが作成されていない
   - エラー: Student model (Student, Seat, Bus等) のテーブルが存在しない

### 問題の原因

- Student側のマイグレーションが正常に実行されていない
- 統合認証システムがStudent用テーブルの存在を前提としている
- Admin側のテーブル（users, permissions）のみ作成済み

## テストユーザー情報

### 作成されるテストユーザー
| ユーザー名 | パスワード | ロール | メール |
|---|---|---|---|
| `admin_test` | `admin123` | admin | admin@test.com |
| `normal_test` | `normal123` | normal | normal@test.com |
| `guest_test` | `guest123` | guest | guest@test.com |

## 使用方法

### 1. データベースとテストユーザーの初期化
```bash
# Dockerコンテナ内で実行
docker exec -it test-admin-1 python test/setup_db.py
```

### 2. ログイン認証テスト
```bash
# データベース直接テスト
docker exec -it test-admin-1 python test/test_login_direct.py

# API経由テスト（ホストマシンで実行、requests必要）
python admin/test/test_auth_api.py
```

### 3. curl での認証テスト
```bash
# admin_test でログイン
curl -k -X POST "https://localhost/admin/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin_test","password":"admin123"}'

# normal_test でログイン
curl -k -X POST "https://localhost/admin/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"normal_test","password":"normal123"}'

# guest_test でログイン  
curl -k -X POST "https://localhost/admin/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"guest_test","password":"guest123"}'
```

## 注意事項

- `setup_db.py`は初期化用スクリプトです。既存データがある場合は上書きされません
- 循環インポートの問題により、Flask ORM経由のスクリプトは現在動作しません
- API テストには`requests`ライブラリが必要です
- Docker環境での実行を前提としています

## トラブルシューティング

### 1. ログインが失敗する場合

**Admin API直接アクセス**（推奨）:
```bash
# 現在確実に動作する方法
curl -k -X POST "https://localhost/admin/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin_test","password":"admin123"}'
```

**統合ログインページでエラーが出る場合**:
- Student側のテーブル作成が必要
- 現在は500エラーが発生（Student model未作成）

### 2. 認証状態の確認

```bash
# トークンの有効性確認
curl -k -X GET "https://localhost/admin/api/auth/check" \
  -H "X-Service-Auth: [取得したトークン]"
```

### 3. データベース状態の確認

```bash
# テーブル一覧確認
docker exec -it test-postgres-1 psql -U user -d mydb -c "\dt"

# ユーザー一覧確認
docker exec -it test-admin-1 python test/setup_db.py list
```
