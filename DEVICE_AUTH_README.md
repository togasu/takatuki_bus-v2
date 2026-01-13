# ドライバーデバイス認証システム - 実装完了

## 実装内容

ドライバーユーザーに対して、最大5台のデバイスを登録し、登録されたデバイスからのアクセス時にパスワード不要でログインできる機能を実装しました。

## 作成されたファイル

### 1. 管理システム (Admin)

#### モデル
- **`admin/app/models/driver_device.py`**
  - `DriverDevice` モデル: デバイス管理テーブル
  - MACアドレスの正規化機能
  - デバイスの追加・削除・検証メソッド
  - 最大5台の制限機能

#### API
- **`admin/app/api/driver_devices.py`**
  - `GET /api/driver-devices/{username}`: デバイス一覧取得
  - `POST /api/driver-devices/{username}`: デバイス追加
  - `DELETE /api/driver-devices/{username}/{device_id}`: デバイス削除
  - `POST /api/driver-devices/{username}/verify`: デバイス検証
  - `GET /api/driver-devices`: 全デバイス一覧取得

#### UI
- **`admin/app/templates/driver_devices.html`**
  - デバイス管理画面
  - ドライバー検索機能
  - デバイスの追加・削除・一覧表示
  - 統計情報の表示

#### ダッシュボード統合
- **`admin/app/templates/admin_dashboard.html`** (更新)
  - ドライバーデバイス管理カードを追加

#### マイグレーション
- **`admin/migrate_driver_devices.py`**
  - `driver_devices` テーブルを作成するマイグレーションスクリプト

#### 権限設定
- **`admin/init_permissions.py`** (更新)
  - `driver_device` リソースに対する権限を追加
    - `create`, `read`, `update`, `delete`

### 2. ドライバーシステム (Driver)

#### 認証ユーティリティ
- **`driver/app/utils/auth_utils.py`** (更新)
  - `DeviceAuthManager` クラスを追加
  - MACアドレス取得機能
  - 管理システムAPIとの連携
  - デバイス認証機能

#### ルーティング
- **`driver/app/index.py`** (更新)
  - `/driver/{username}` ルートを追加
  - MACアドレスベースの自動ログイン機能
  - セッション自動作成

#### クライアント側JavaScript
- **`driver/app/static/js/device_auth.js`**
  - デバイスフィンガープリント生成
  - デバイスID自動送信
  - LocalStorageによるID保存
  - デバッグモード対応

### 3. ドキュメント

- **`docs/device-authentication.md`**
  - 完全な実装ガイド
  - MACアドレス取得方法の詳細
  - セキュリティ上の注意事項

- **`docs/device-auth-quickstart.md`**
  - クイックスタートガイド
  - APIエンドポイント一覧
  - トラブルシューティング

### 4. テストスクリプト

- **`test_device_auth.py`**
  - デバイス登録テスト
  - デバイス一覧取得テスト
  - デバイス検証テスト
  - 最大台数制限テスト

## セットアップ手順

### 1. データベースマイグレーション

```powershell
cd admin
python migrate_driver_devices.py
```

### 2. 権限の初期化

```powershell
cd admin
python init_permissions.py
```

### 3. HTMLテンプレートの更新

driver側のベーステンプレート（例: `driver/app/templates/base.html`）に以下を追加:

```html
<script src="{{ url_for('static', filename='js/device_auth.js') }}"></script>
```

### 4. 環境変数の設定

`driver/.env` に以下を追加:

```
ADMIN_API_URL=http://admin:5000
```

### 5. システムの再起動

```powershell
docker-compose down
docker-compose up -d
```

## 使用方法

### デバイスの登録（管理者）

#### 方法1: Web UI（推奨）

1. 管理ダッシュボードにアクセス: `https://localhost/admin/`
2. 「ドライバーデバイス管理」カードをクリック
3. 「ドライバーを選択」ボタンをクリック
4. ドライバー名を入力（例: driver1）
5. 「デバイス追加」ボタンをクリック
6. MACアドレスとデバイス名を入力
7. 「追加」ボタンをクリック

詳細は[driver-device-ui-guide.md](./docs/driver-device-ui-guide.md)を参照してください。

#### 方法2: API経由

```python
import requests

response = requests.post(
    "https://localhost/admin/api/driver-devices/driver1",
    json={
        "mac_address": "AA:BB:CC:DD:EE:FF",
        "device_name": "運転席タブレット"
    },
    headers={"Authorization": f"Bearer {admin_token}"}
)
```

### デバイスログイン（ドライバー）

登録されたデバイスから以下のURLにアクセス:

```
https://localhost/driver/driver1
```

JavaScriptが自動的にデバイスIDを送信し、登録されていればパスワード不要でログインされます。

## 技術的詳細

### MACアドレスの取得について

HTTPリクエストでは通常MACアドレスを直接取得できないため、以下の代替手段を提供:

1. **デバイスフィンガープリント（推奨）**
   - Canvas、WebGL、画面情報などからハッシュを生成
   - ブラウザベースで動作
   - `device_auth.js` で実装済み

2. **VPN環境でのARPテーブル参照**
   - サーバー側でIPアドレスからMACアドレスを取得
   - 同一ネットワーク内でのみ動作

3. **DHCP連携**
   - DHCPサーバーのログを参照
   - 最も確実だが設定が複雑

### セキュリティ

- MACアドレス（デバイスID）は偽装可能なため、追加のセキュリティ対策を推奨
- HTTPS必須（本番環境）
- 定期的なデバイス監査
- アクセスログの監視

## テスト

```powershell
# テストスクリプトの実行
python test_device_auth.py
```

## トラブルシューティング

詳細は `docs/device-auth-quickstart.md` を参照してください。

### よくある問題

1. **デバイス認証が失敗する**
   - デバイスIDを確認: `https://localhost/driver/driver1?debug=true`
   - 登録状態を確認
   - サーバーログを確認

2. **JavaScriptが動作しない**
   - ブラウザコンソールでエラーを確認
   - スクリプトが読み込まれているか確認
   - HTTPS環境で実行されているか確認

## 今後の拡張

- UIによるデバイス管理画面
- デバイス使用統計
- 一時的なデバイス許可機能
- 多要素認証との組み合わせ

## 関連ドキュメント

- [device-authentication.md](./docs/device-authentication.md) - 完全な実装ガイド
- [device-auth-quickstart.md](./docs/device-auth-quickstart.md) - クイックスタート
- [driver-device-ui-guide.md](./docs/driver-device-ui-guide.md) - UI使用ガイド
- [admin-service.md](./docs/admin-service.md) - 管理システム
- [driver-service.md](./docs/driver-service.md) - ドライバーシステム
