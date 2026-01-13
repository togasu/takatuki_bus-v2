# ドライバーデバイス認証システム

## 概要
ドライバーが登録されているMACアドレス（またはデバイスID）からのみログインできるセキュリティ機能です。

## 仕組み

### 1. デバイス登録
管理者が事前にドライバーのデバイス（タブレット、PCなど）のMACアドレスを登録します：
- 各ドライバーは最大5台までデバイスを登録可能
- MACアドレスは正規化されて保存（XX:XX:XX:XX:XX:XX形式）
- 有効/無効の管理が可能

### 2. 認証方法

#### A. 特殊ログイン（/login1, /login2, /login3...）
- **完全なデバイス認証必須**
- パスワード不要
- 登録済みデバイスからのみアクセス可能
- 使用例: `https://localhost/driver/login1`

#### B. 通常ログイン（username + password）
- パスワード認証のみ（現在の実装）
- デバイス認証は任意で追加可能

### 3. デバイス識別方法

ブラウザから直接MACアドレスを取得することはできないため、以下の方法を使用します：

#### 方法1: ブラウザフィンガープリント（推奨）
```javascript
// 自動生成される一意のデバイスID
- UserAgent
- 画面解像度
- タイムゾーン
- Canvas fingerprint
などを組み合わせてハッシュ化
```

#### 方法2: 手動入力（管理者向け）
```
URLに ?debug=1 を追加してアクセス
→ MACアドレス手動入力プロンプトが表示
→ 登録済みのMACアドレスを入力
```

#### 方法3: ネイティブアプリ（将来的）
専用アプリから実際のMACアドレスを送信

## セットアップ手順

### 1. デバイスを登録する

#### 管理画面から登録：
1. Admin画面にアクセス: `https://localhost/admin`
2. 「ドライバーデバイス管理」メニューを選択
3. 対象ドライバーを選択
4. 「デバイス追加」ボタンをクリック
5. MACアドレスを入力（自動または手動）

#### APIから登録：
```bash
curl -X POST https://localhost/admin/api/driver-devices \
  -H "Content-Type: application/json" \
  -d '{
    "driver_id": 1,
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "device_name": "運転席タブレット"
  }'
```

### 2. デバイスIDを確認する

#### ブラウザで確認：
1. ドライバーログインページを開く
2. ページ下部に「デバイスID: XX:XX:XX:XX:XX:XX」と表示される
3. このIDを管理者に伝えて登録してもらう

#### デバッグモードで確認：
```
https://localhost/driver/login?debug=1
```

### 3. 特殊ログインを使用する

登録後、以下のURLでパスワード不要でログイン可能：
```
driver1 → https://localhost/driver/login1
driver2 → https://localhost/driver/login2
driver3 → https://localhost/driver/login3
```

## テスト方法

### 開発環境でのテスト

1. **デバイスIDを手動設定**:
   ```
   https://localhost/driver/login?debug=1
   ```
   表示されるプロンプトにMACアドレスを入力
   例: `AA:BB:CC:DD:EE:FF`

2. **管理画面でデバイス登録**:
   - driver1のIDを1として、上記MACアドレスを登録

3. **特殊ログインでテスト**:
   ```
   https://localhost/driver/login1
   ```
   → 登録済みデバイスの場合: ログイン成功
   → 未登録デバイスの場合: 「このデバイスは登録されていません」

### 本番環境での運用

1. **タブレットでログインページを開く**
   - 自動的にデバイスフィンガープリントが生成される
   - デバイスIDが画面下部に表示される

2. **デバイスIDを管理者に伝える**
   - 管理者がAdmin画面でデバイスを登録

3. **以降は特殊ログインが使用可能**

## セキュリティ注意事項

### デバイスフィンガープリントの限界
- ブラウザのアップデートで変わる可能性がある
- プライベートモードでは異なるIDになる
- 完全な一意性は保証されない

### 推奨事項
1. **デバイスIDの定期的な再確認**
2. **複数デバイスの登録** （予備として）
3. **最終使用日時の監視** （不正アクセス検知）
4. **パスワード認証との併用** （通常ログイン）

## トラブルシューティング

### 「デバイス認証失敗」エラー

**原因**:
- デバイスが未登録
- MACアドレスが変わった
- ブラウザのキャッシュをクリアした

**対処**:
1. デバイスIDを確認
2. 管理者に再登録を依頼
3. または通常のパスワードログインを使用

### デバイスIDが毎回変わる

**原因**:
- プライベートモード使用
- LocalStorageが無効
- Cookieが無効

**対処**:
1. 通常モードで使用
2. ブラウザ設定でCookieとLocalStorageを有効化

## API仕様

### デバイス登録
```
POST /admin/api/driver-devices
{
  "driver_id": 1,
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "device_name": "タブレット1"
}
```

### デバイス一覧取得
```
GET /admin/api/driver-devices?driver_id=1
```

### デバイス削除
```
DELETE /admin/api/driver-devices/{device_id}
```

### 認証検証
```python
from app.utils.device_auth import validate_device_access

success, message, device = validate_device_access(driver_id=1)
if success:
    # 認証成功
    device.update_last_used()
```

## 実装詳細

### ファイル構成
```
driver/
├── app/
│   ├── models/
│   │   └── driver_device.py      # デバイスモデル
│   ├── utils/
│   │   └── device_auth.py        # 認証ユーティリティ
│   ├── routes/
│   │   └── main_routes.py        # ログインルート
│   └── templates/
│       └── login.html            # ログインページ
```

### データベーススキーマ
```sql
CREATE TABLE driver_devices (
    id SERIAL PRIMARY KEY,
    driver_id INTEGER REFERENCES drivers(id),
    mac_address VARCHAR(17) NOT NULL,
    device_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_used_at TIMESTAMP,
    UNIQUE (driver_id, mac_address)
);
```

## 今後の拡張

1. **ネイティブアプリ対応**
   - 実際のMACアドレス取得
   - より確実なデバイス認証

2. **生体認証の追加**
   - 指紋認証
   - 顔認証

3. **2段階認証**
   - SMSコード
   - TOTPアプリ

4. **位置情報認証**
   - GPS座標チェック
   - 営業所内のみログイン可能
