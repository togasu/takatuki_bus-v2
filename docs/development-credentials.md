# 開発環境 認証情報

このドキュメントには、開発環境で使用するテストアカウントの認証情報が記載されています。

> ⚠️ **警告**: このドキュメントは開発環境専用です。本番環境では絶対に使用しないでください。

---

## 📋 目次

- [サービスURL](#サービスurl)
- [管理者アカウント (Admin)](#管理者アカウント-admin)
- [ドライバーアカウント (Driver)](#ドライバーアカウント-driver)
- [学生アカウント (Student)](#学生アカウント-student)
- [データベース接続情報](#データベース接続情報)
- [Redis接続情報](#redis接続情報)
- [API認証トークン](#api認証トークン)

---

## 🌐 サービスURL

### HTTPS (推奨)
- **Student Service**: https://localhost/
- **Admin Service**: https://localhost/admin/
- **Driver Service**: https://localhost/driver/

### HTTP (開発用)
- **Student Service**: http://localhost/
- **Admin Service**: http://localhost/admin/
- **Driver Service**: http://localhost/driver/

---

## 👤 管理者アカウント (Admin)

### テストアカウント

| 項目 | 値 |
|------|-----|
| **ユーザー名** | `admin_test` |
| **パスワード** | `admin123` |
| **メールアドレス** | `admin@test.com` |
| **権限レベル** | Admin (最高権限) |

### ログイン方法

1. ブラウザで https://localhost/admin/ にアクセス
2. ユーザー名: `admin_test`
3. パスワード: `admin123`
4. ログインボタンをクリック

### 作成スクリプト

テストアカウントは以下のスクリプトで作成されます:

```bash
# Docker内で実行
docker-compose exec admin python create_test_admin.py
```

### 利用可能な機能

- ✅ 学生管理（一覧、詳細、編集、削除）
- ✅ ドライバー管理
- ✅ バス管理
- ✅ 予約管理
- ✅ 学期管理
- ✅ ペナルティ管理
- ✅ システム設定
- ✅ 権限管理

---

## 🚗 ドライバーアカウント (Driver)

### テストアカウント

| 項目 | 値 |
|------|-----|
| **ドライバーID** | `driver_test` |
| **パスワード** | `driver123` |
| **名前** | `テストドライバー` |
| **メールアドレス** | `driver@test.com` |
| **電話番号** | `090-1234-5678` |
| **免許証番号** | `TEST-123456789` |
| **免許証有効期限** | `2026-12-31` |
| **雇用日** | `2024-01-01` |
| **ステータス** | 有効 (is_active: true) |

### ログイン方法

1. ブラウザで https://localhost/driver/ にアクセス
2. ドライバーID: `driver_test`
3. パスワード: `driver123`
4. ログインボタンをクリック

### 作成スクリプト

テストアカウントは以下のスクリプトで作成されます:

```bash
# Docker内で実行
docker-compose exec driver python create_test_driver.py
```

### 利用可能な機能

- ✅ 予約一覧表示
- ✅ 予約詳細確認
- ✅ 出席確認
- ✅ Q&A機能（質問と回答）
- ✅ プロフィール表示

---

## 🎓 学生アカウント (Student)

学生アカウントはLDAP認証を使用します。

### テストアカウント作成

```bash
# Docker内で実行
docker-compose exec student python create_test_student.py
```

### LDAPテストアカウント

| 項目 | 値 |
|------|-----|
| **学籍番号** | （LDAP設定による） |
| **パスワード** | （LDAP設定による） |

詳細は `test_ldap_login.py` を参照してください。

### 利用可能な機能

- ✅ バス予約
- ✅ 予約履歴表示
- ✅ 予約キャンセル
- ✅ ペナルティ確認
- ✅ プロフィール表示

---

## 🗄️ データベース接続情報

### PostgreSQL

| 項目 | 値 |
|------|-----|
| **ホスト** | `postgres` (Docker内) / `localhost` (ホストから) |
| **ポート** | `5432` |
| **データベース名** | `mydb` |
| **ユーザー名** | `user` |
| **パスワード** | `pass` |

### 接続例

```bash
# Docker内から
psql -h postgres -U user -d mydb

# ホストから
psql -h localhost -U user -d mydb
```

### 接続URI

```
postgresql://user:pass@postgres:5432/mydb
```

---

## 🔴 Redis接続情報

| 項目 | 値 |
|------|-----|
| **ホスト** | `redis` (Docker内) / `localhost` (ホストから) |
| **ポート** | `6379` |
| **パスワード** | なし |

### 接続例

```bash
# Docker内から
redis-cli -h redis

# ホストから
redis-cli -h localhost
```

---

## 🔑 API認証トークン

### サービス間通信用トークン

| 項目 | 値 |
|------|-----|
| **Admin Service Token** | `admin-secret-token-2024` |
| **API Secret Key** | `bus-system-api-key-2024` |

### 使用例

```bash
# Admin APIへのリクエスト例
curl -X GET https://localhost/admin/api/students \
  -H "X-Admin-Token: admin-secret-token-2024" \
  -H "Content-Type: application/json"
```

---

## 🔧 トラブルシューティング

### アカウントが作成されていない場合

```bash
# 各サービスのテストアカウント作成スクリプトを実行
docker-compose exec admin python create_test_admin.py
docker-compose exec driver python create_test_driver.py
docker-compose exec student python create_test_student.py
```

### ログインできない場合

1. データベースにアカウントが存在するか確認:

```bash
# Adminアカウント確認
docker-compose exec postgres psql -U user -d mydb -c "SELECT username, email, role FROM users WHERE username='admin_test';"

# Driverアカウント確認
docker-compose exec postgres psql -U user -d mydb -c "SELECT driver_id, name, email FROM drivers WHERE driver_id='driver_test';"
```

2. パスワードが正しいか確認（上記の認証情報を参照）

3. アカウントが有効化されているか確認:

```bash
# Adminアカウント
docker-compose exec postgres psql -U user -d mydb -c "SELECT username, is_active FROM users WHERE username='admin_test';"

# Driverアカウント
docker-compose exec postgres psql -U user -d mydb -c "SELECT driver_id, is_active FROM drivers WHERE driver_id='driver_test';"
```

### セッションが切れる場合

Redisが起動しているか確認:

```bash
docker-compose ps redis
```

---

## 📝 注意事項

### セキュリティ

- ⚠️ このドキュメントの内容は**開発環境専用**です
- ⚠️ 本番環境では**絶対に**これらの認証情報を使用しないでください
- ⚠️ 本番環境では強力なパスワードと適切な認証方式を使用してください
- ⚠️ このファイルをGitHubなどの公開リポジトリにコミットしないでください

### 推奨事項

- 本番環境用の認証情報は環境変数または秘密管理サービスで管理してください
- 定期的にパスワードを変更してください
- 不要になったテストアカウントは削除してください

---

## 🔗 関連ドキュメント

- [起動ガイド](startup-guide.md)
- [Admin Service](admin-service.md)
- [Driver Service](driver-service.md)
- [Student Service](student-service.md)
- [権限システム](permissions-system.md)

---

**最終更新日**: 2025年11月7日
