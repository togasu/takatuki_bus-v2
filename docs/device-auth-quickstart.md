# デバイス認証システム - クイックスタートガイド

## 1. セットアップ

### データベースマイグレーション

```powershell
# admin システムでデバイステーブルを作成
cd admin
python migrate_driver_devices.py
```

### 権限の初期化

```powershell
# 権限システムを初期化（ドライバーデバイス権限を含む）
cd admin
python init_permissions.py
```

## 2. デバイスの登録（管理者）

### API経由での登録

```python
import requests

# 管理者としてログイン後、トークンを取得
admin_token = "your_admin_token"

# ドライバー "driver1" に3台のデバイスを登録
devices = [
    {"mac": "AA:BB:CC:DD:EE:01", "name": "運転席タブレット1"},
    {"mac": "AA:BB:CC:DD:EE:02", "name": "運転席タブレット2"},
    {"mac": "AA:BB:CC:DD:EE:03", "name": "予備端末"},
]

for device in devices:
    response = requests.post(
        "https://localhost/admin/api/driver-devices/driver1",
        json={
            "mac_address": device["mac"],
            "device_name": device["name"]
        },
        headers={"Authorization": f"Bearer {admin_token}"},
        verify=False
    )
    print(f"登録: {device['name']} - {response.status_code}")
```

### 登録されたデバイスの確認

```python
response = requests.get(
    "https://localhost/admin/api/driver-devices/driver1",
    headers={"Authorization": f"Bearer {admin_token}"},
    verify=False
)

data = response.json()
print(f"登録デバイス数: {data['device_count']}/{data['max_devices']}")
for device in data['devices']:
    print(f"  - {device['device_name']}: {device['mac_address']}")
```

## 3. デバイスログインの使用（ドライバー）

### 方法1: JavaScriptによる自動デバイスID送信

1. driver側のHTMLテンプレートに以下のスクリプトを追加:

```html
<!-- driver/app/templates/base.html など -->
<script src="{{ url_for('static', filename='js/device_auth.js') }}"></script>
```

2. 登録されたデバイスから以下のURLにアクセス:

```
https://localhost/driver/driver1
```

デバイスが登録されていれば、自動的にログインされます。

### 方法2: カスタムヘッダーを使用

```python
import requests

# デバイスのMACアドレス（またはデバイスID）
device_mac = "AA:BB:CC:DD:EE:01"

response = requests.get(
    "https://localhost/driver/driver1",
    headers={"X-Client-MAC": device_mac},
    verify=False
)

if response.status_code == 200:
    print("ログイン成功!")
```

## 4. デバイスIDの取得（クライアント側）

ブラウザコンソールで以下を実行:

```javascript
// 現在のデバイスIDを取得
const deviceId = await window.DeviceAuth.getDeviceId();
console.log("Device ID:", deviceId);

// デバイスIDを再生成（テスト用）
const newId = await window.DeviceAuth.regenerateDeviceId();
console.log("New Device ID:", newId);
```

デバッグモードで表示:
```
https://localhost/driver/driver1?debug=true
```

画面右下にデバイスIDが表示されます。

## 5. デバイスの管理

### デバイスの削除

```python
# デバイスIDを指定して削除
device_id = 1
response = requests.delete(
    f"https://localhost/admin/api/driver-devices/driver1/{device_id}",
    headers={"Authorization": f"Bearer {admin_token}"},
    verify=False
)
```

### 全ドライバーのデバイス一覧

```python
response = requests.get(
    "https://localhost/admin/api/driver-devices",
    headers={"Authorization": f"Bearer {admin_token}"},
    verify=False
)

data = response.json()
print(f"総ユーザー数: {data['total_users']}")
print(f"総デバイス数: {data['total_devices']}")
```

## 6. トラブルシューティング

### デバイス認証が失敗する

1. **デバイスIDを確認**
   ```
   https://localhost/driver/driver1?debug=true
   ```
   
2. **登録状態を確認**
   ```python
   response = requests.post(
       "https://localhost/admin/api/driver-devices/driver1/verify",
       json={"mac_address": "AA:BB:CC:DD:EE:01"},
       headers={"Authorization": f"Bearer {admin_token}"},
       verify=False
   )
   print(response.json())
   ```

3. **サーバーログを確認**
   ```powershell
   # driver側のログ
   docker-compose logs driver
   
   # admin側のログ
   docker-compose logs admin
   ```

### JavaScriptが動作しない

1. ブラウザコンソールでエラーを確認
2. `device_auth.js` が正しく読み込まれているか確認
3. HTTPS環境で実行されているか確認（LocalStorage使用のため）

## 7. セキュリティ上の注意

1. **本番環境では必ずHTTPSを使用**
2. **定期的にデバイスリストを監査**
3. **不要なデバイスは速やかに削除**
4. **異常なログインパターンを監視**

## 8. APIエンドポイント一覧

| メソッド | エンドポイント | 説明 |
|---------|--------------|------|
| GET | `/api/driver-devices/{username}` | デバイス一覧取得 |
| POST | `/api/driver-devices/{username}` | デバイス追加 |
| DELETE | `/api/driver-devices/{username}/{device_id}` | デバイス削除 |
| POST | `/api/driver-devices/{username}/verify` | デバイス検証 |
| GET | `/api/driver-devices` | 全デバイス一覧 |

## 9. テストの実行

```powershell
# テストスクリプトを実行
python test_device_auth.py
```

## 詳細ドキュメント

詳細な情報は以下を参照してください:
- [device-authentication.md](./device-authentication.md) - 完全な実装ガイド
- [admin-service.md](./admin-service.md) - 管理システム全般
- [driver-service.md](./driver-service.md) - ドライバーシステム全般
