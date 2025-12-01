# ドライバーデバイス認証システム

## 概要

このシステムは、管理者が登録した最大5台のデバイスからのアクセスに限り、ドライバーがパスワードなしでログインできる機能を提供します。

## 機能

1. **管理システム (Admin)**
   - ドライバーごとに最大5台のMACアドレスを登録可能
   - デバイスの追加・削除・一覧表示
   - デバイス認証状態の確認

2. **ドライバーシステム (Driver)**
   - 登録済みデバイスからのアクセス時、パスワード不要でログイン
   - URL: `https://localhost/driver/{username}`

## セットアップ手順

### 1. データベースマイグレーション

```powershell
cd admin
python migrate_driver_devices.py
```

### 2. 権限設定

管理システムで以下の権限を設定してください:

```python
# admin/init_permissions.py に追加
{
    "resource": "driver_device",
    "actions": ["create", "read", "update", "delete"],
    "description": "ドライバーデバイス管理"
}
```

### 3. MACアドレスの取得方法

HTTPリクエストでは通常MACアドレスを直接取得できません。以下のいずれかの方法を実装してください:

#### 方法1: クライアント側JavaScript（推奨）

```javascript
// driver/app/static/js/mac_address.js
async function getMacAddress() {
    try {
        // ブラウザのAPI制限により、完全なMACアドレスは取得できない
        // 代わりにフィンガープリント技術を使用
        
        // ユーザーエージェント、画面解像度、タイムゾーンなどから
        // デバイス固有のハッシュを生成
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('Device fingerprint', 0, 0);
        
        const deviceInfo = {
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            screenResolution: `${screen.width}x${screen.height}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            canvasFingerprint: canvas.toDataURL()
        };
        
        // ハッシュ化してデバイスIDを生成
        const deviceId = await crypto.subtle.digest(
            'SHA-256',
            new TextEncoder().encode(JSON.stringify(deviceInfo))
        );
        
        const hashArray = Array.from(new Uint8Array(deviceId));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        
        // MACアドレス風の形式に変換
        return hashHex.substring(0, 12).match(/.{1,2}/g).join(':').toUpperCase();
    } catch (error) {
        console.error('Error generating device ID:', error);
        return null;
    }
}

// ページロード時にMACアドレスをヘッダーに設定
window.addEventListener('DOMContentLoaded', async () => {
    const macAddress = await getMacAddress();
    if (macAddress) {
        // すべてのfetchリクエストにヘッダーを追加
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            if (args[1]) {
                args[1].headers = {
                    ...args[1].headers,
                    'X-Client-MAC': macAddress
                };
            } else {
                args[1] = {
                    headers: {
                        'X-Client-MAC': macAddress
                    }
                };
            }
            return originalFetch.apply(this, args);
        };
    }
});
```

#### 方法2: VPN環境でのARPテーブル参照（企業向け）

VPNで管理されたネットワーク内で、サーバー側でARPテーブルを参照してMACアドレスを取得:

```python
# driver/app/utils/network_utils.py
import subprocess
import re

def get_mac_from_ip(ip_address: str) -> str:
    """
    ARPテーブルからIPアドレスに対応するMACアドレスを取得
    注意: 同一ネットワーク内でのみ動作
    """
    try:
        # Windowsの場合
        result = subprocess.run(['arp', '-a', ip_address], 
                              capture_output=True, text=True)
        
        # MACアドレスのパターンをマッチング
        mac_pattern = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
        match = re.search(mac_pattern, result.stdout)
        
        if match:
            return match.group(0).replace('-', ':').upper()
        
        return None
    except Exception as e:
        print(f"Error getting MAC from ARP: {e}")
        return None
```

#### 方法3: DHCP連携（最も確実）

DHCPサーバーのログから、IPアドレスとMACアドレスのマッピングを取得し、Redisなどに保存して参照する方法。

### 4. 環境変数の設定

```bash
# driver/.env に追加
ADMIN_API_URL=http://admin:5000
```

## API エンドポイント

### ドライバーデバイス管理 API

#### デバイス一覧取得
```http
GET /api/driver-devices/{username}
Authorization: Bearer {token}
```

#### デバイス追加
```http
POST /api/driver-devices/{username}
Content-Type: application/json

{
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "device_name": "運転席タブレット1"
}
```

#### デバイス削除
```http
DELETE /api/driver-devices/{username}/{device_id}
Authorization: Bearer {token}
```

#### デバイス検証
```http
POST /api/driver-devices/{username}/verify
Content-Type: application/json

{
    "mac_address": "AA:BB:CC:DD:EE:FF"
}
```

## 使用例

### 1. デバイスを登録（管理者側）

```python
import requests

# 管理システムにログイン後
response = requests.post(
    'https://localhost/admin/api/driver-devices/driver1',
    json={
        'mac_address': 'AA:BB:CC:DD:EE:FF',
        'device_name': 'タブレット1'
    },
    headers={'Authorization': f'Bearer {admin_token}'}
)
```

### 2. デバイスからログイン（ドライバー側）

登録済みデバイスから以下のURLにアクセス:
```
https://localhost/driver/driver1
```

MACアドレスが登録されていれば、パスワード入力なしで自動的にログインされます。

### 3. デバイス一覧の確認

```python
response = requests.get(
    'https://localhost/admin/api/driver-devices/driver1',
    headers={'Authorization': f'Bearer {admin_token}'}
)

print(response.json())
# {
#     "success": true,
#     "username": "driver1",
#     "device_count": 2,
#     "max_devices": 5,
#     "devices": [...]
# }
```

## セキュリティ上の注意

1. **MACアドレスの偽装リスク**
   - MACアドレスは偽装可能なため、追加のセキュリティ対策を推奨
   - デバイスフィンガープリントと組み合わせる
   - 異常なアクセスパターンを監視

2. **HTTPS必須**
   - 本番環境では必ずHTTPSを使用
   - MACアドレス情報の盗聴を防ぐ

3. **定期的なデバイス監査**
   - 登録デバイスを定期的に確認
   - 不要なデバイスは削除

4. **アクセスログの監視**
   - デバイス認証によるログインを記録
   - 異常なアクセスを検出

## トラブルシューティング

### デバイス認証が失敗する

1. MACアドレスが正しく取得されているか確認
   - ブラウザのコンソールでMACアドレスを出力
   - サーバーログで受信したMACアドレスを確認

2. デバイスが登録されているか確認
   ```bash
   curl -X POST https://localhost/admin/api/driver-devices/driver1/verify \
     -H "Content-Type: application/json" \
     -d '{"mac_address": "AA:BB:CC:DD:EE:FF"}'
   ```

3. 管理システムとドライバーシステム間の通信を確認
   - ネットワーク接続
   - ファイアウォール設定

### データベースエラー

マイグレーションを再実行:
```bash
cd admin
python migrate_driver_devices.py
```

## 今後の拡張案

1. **デバイス使用統計**
   - デバイスごとのログイン回数
   - 最終使用日時の追跡

2. **一時的なデバイス許可**
   - 期間限定でデバイスを許可
   - 自動無効化

3. **多要素認証**
   - デバイス認証 + ワンタイムパスワード
   - 生体認証との組み合わせ

4. **デバイスグループ管理**
   - 複数ドライバーで同じデバイスを共有
   - デバイスプール管理
