"""
ドライバーデバイス認証システムのテスト用スクリプト

使用方法:
    python test_device_auth.py
"""
import requests
import json

# テスト用の設定
ADMIN_URL = "https://localhost/admin"
DRIVER_URL = "https://localhost/driver"
TEST_USERNAME = "driver1"
TEST_MAC_ADDRESSES = [
    "AA:BB:CC:DD:EE:01",
    "AA:BB:CC:DD:EE:02",
    "AA:BB:CC:DD:EE:03",
    "AA:BB:CC:DD:EE:04",
    "AA:BB:CC:DD:EE:05",
]

def test_device_registration():
    """デバイス登録のテスト"""
    print("=" * 60)
    print("デバイス登録テスト")
    print("=" * 60)
    
    # 注意: 実際には管理者認証が必要です
    # ここでは簡略化のため、認証部分は省略しています
    
    for i, mac in enumerate(TEST_MAC_ADDRESSES[:3], 1):
        print(f"\nデバイス {i} を登録中...")
        print(f"  MAC Address: {mac}")
        
        # デバイス登録APIを呼び出し
        # 実際の使用時はここに認証トークンを含める必要があります
        response = requests.post(
            f"{ADMIN_URL}/api/driver-devices/{TEST_USERNAME}",
            json={
                "mac_address": mac,
                "device_name": f"テストデバイス {i}"
            },
            verify=False  # 開発環境用（本番では削除）
        )
        
        if response.status_code == 201:
            print("  ✓ 登録成功")
            print(f"  レスポンス: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"  ✗ 登録失敗: {response.status_code}")
            print(f"  エラー: {response.text}")

def test_device_list():
    """デバイス一覧取得のテスト"""
    print("\n" + "=" * 60)
    print("デバイス一覧取得テスト")
    print("=" * 60)
    
    response = requests.get(
        f"{ADMIN_URL}/api/driver-devices/{TEST_USERNAME}",
        verify=False
    )
    
    if response.status_code == 200:
        print("✓ 取得成功")
        data = response.json()
        print(f"\n登録デバイス数: {data['device_count']}/{data['max_devices']}")
        print("\nデバイス一覧:")
        for device in data['devices']:
            print(f"  - ID: {device['id']}")
            print(f"    MAC: {device['mac_address']}")
            print(f"    名前: {device['device_name']}")
            print(f"    状態: {'有効' if device['is_active'] else '無効'}")
            print()
    else:
        print(f"✗ 取得失敗: {response.status_code}")
        print(f"エラー: {response.text}")

def test_device_verification():
    """デバイス検証のテスト"""
    print("\n" + "=" * 60)
    print("デバイス検証テスト")
    print("=" * 60)
    
    # 登録済みデバイスの検証
    print("\n1. 登録済みデバイスの検証")
    response = requests.post(
        f"{ADMIN_URL}/api/driver-devices/{TEST_USERNAME}/verify",
        json={"mac_address": TEST_MAC_ADDRESSES[0]},
        verify=False
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"  MAC: {data['mac_address']}")
        print(f"  登録状態: {'登録済み' if data['is_registered'] else '未登録'}")
    else:
        print(f"  ✗ 検証失敗: {response.status_code}")
    
    # 未登録デバイスの検証
    print("\n2. 未登録デバイスの検証")
    response = requests.post(
        f"{ADMIN_URL}/api/driver-devices/{TEST_USERNAME}/verify",
        json={"mac_address": "FF:FF:FF:FF:FF:FF"},
        verify=False
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"  MAC: {data['mac_address']}")
        print(f"  登録状態: {'登録済み' if data['is_registered'] else '未登録'}")
    else:
        print(f"  ✗ 検証失敗: {response.status_code}")

def test_device_login():
    """デバイスログインのテスト"""
    print("\n" + "=" * 60)
    print("デバイスログインテスト")
    print("=" * 60)
    
    print("\n注意: このテストはMACアドレスをヘッダーに含める必要があります")
    print("ブラウザまたはクライアント側JavaScriptからのテストを推奨します")
    
    # ヘッダーにMACアドレスを含めてリクエスト
    headers = {
        "X-Client-MAC": TEST_MAC_ADDRESSES[0]
    }
    
    response = requests.get(
        f"{DRIVER_URL}/{TEST_USERNAME}",
        headers=headers,
        verify=False,
        allow_redirects=False
    )
    
    print(f"\nステータスコード: {response.status_code}")
    if response.status_code == 200:
        print("✓ ログイン成功")
    else:
        print(f"レスポンス: {response.text[:200]}...")

def test_max_devices():
    """最大デバイス数制限のテスト"""
    print("\n" + "=" * 60)
    print("最大デバイス数制限テスト")
    print("=" * 60)
    
    print("\n5台を超えるデバイスの登録を試行...")
    
    # 6台目のデバイスを登録しようとする
    response = requests.post(
        f"{ADMIN_URL}/api/driver-devices/{TEST_USERNAME}",
        json={
            "mac_address": "FF:FF:FF:FF:FF:FF",
            "device_name": "6台目（登録不可）"
        },
        verify=False
    )
    
    if response.status_code == 400:
        print("✓ 正しく制限されました")
        print(f"エラーメッセージ: {response.json().get('error')}")
    else:
        print(f"✗ 予期しない結果: {response.status_code}")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("ドライバーデバイス認証システム テストスイート")
    print("=" * 60)
    print("\n警告: SSL証明書の検証を無効化しています（開発環境用）")
    
    # SSL警告を抑制
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        # テストを実行
        test_device_registration()
        test_device_list()
        test_device_verification()
        test_device_login()
        # test_max_devices()  # 必要に応じてコメント解除
        
        print("\n" + "=" * 60)
        print("テスト完了")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ エラー: サーバーに接続できません")
        print("サーバーが起動していることを確認してください")
    except Exception as e:
        print(f"\n✗ エラー: {e}")
        import traceback
        traceback.print_exc()
