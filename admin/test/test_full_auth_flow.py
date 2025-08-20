#!/usr/bin/env python3
"""
認証フローの完全テスト
"""

import json
import requests
import sys

def test_full_auth_flow():
    """完全な認証フローをテスト"""
    base_url = "https://localhost/admin/api"
    
    print("=" * 60)
    print("Admin認証フロー完全テスト")
    print("=" * 60)
    
    # 1. ログインテスト
    print("\n1. ログインテスト")
    login_data = {
        "username": "admin_test",
        "password": "admin123"
    }
    
    try:
        response = requests.post(
            f"{base_url}/auth/login",
            json=login_data,
            verify=False,
            timeout=10
        )
        
        print(f"ログインレスポンス: {response.status_code}")
        
        if response.status_code == 200:
            login_result = response.json()
            print(f"✅ ログイン成功!")
            print(f"   トークン: {login_result.get('token')}")
            print(f"   ユーザーID: {login_result.get('user_id')}")
            print(f"   ロール: {login_result.get('role')}")
            
            token = login_result.get('token')
            
            # 2. 認証チェックテスト
            print("\n2. 認証チェックテスト")
            headers = {"X-Service-Auth": token}
            
            check_response = requests.get(
                f"{base_url}/auth/check",
                headers=headers,
                verify=False,
                timeout=10
            )
            
            print(f"認証チェックレスポンス: {check_response.status_code}")
            if check_response.status_code == 200:
                print("✅ 認証チェック成功!")
                print(f"   結果: {check_response.json()}")
            else:
                print(f"❌ 認証チェック失敗: {check_response.text}")
            
            # 3. ユーザー一覧取得テスト（権限必要）
            print("\n3. ユーザー一覧取得テスト")
            
            users_response = requests.get(
                f"{base_url}/users",
                headers=headers,
                verify=False,
                timeout=10
            )
            
            print(f"ユーザー一覧レスポンス: {users_response.status_code}")
            if users_response.status_code == 200:
                users = users_response.json()
                print(f"✅ ユーザー一覧取得成功! ユーザー数: {len(users)}")
                for user in users:
                    print(f"   - {user.get('username')} ({user.get('role')})")
            else:
                print(f"❌ ユーザー一覧取得失敗: {users_response.text}")
            
            # 4. 権限一覧取得テスト
            print("\n4. 権限一覧取得テスト")
            
            permissions_response = requests.get(
                f"{base_url}/permissions",
                headers=headers,
                verify=False,
                timeout=10
            )
            
            print(f"権限一覧レスポンス: {permissions_response.status_code}")
            if permissions_response.status_code == 200:
                permissions = permissions_response.json()
                print(f"✅ 権限一覧取得成功! 権限数: {len(permissions)}")
                for perm in permissions:
                    print(f"   - {perm.get('permission_name')} ({perm.get('resource')}.{perm.get('action')})")
            else:
                print(f"❌ 権限一覧取得失敗: {permissions_response.text}")
            
            # 5. ログアウトテスト
            print("\n5. ログアウトテスト")
            
            logout_response = requests.post(
                f"{base_url}/auth/logout",
                headers=headers,
                verify=False,
                timeout=10
            )
            
            print(f"ログアウトレスポンス: {logout_response.status_code}")
            if logout_response.status_code == 200:
                print("✅ ログアウト成功!")
            else:
                print(f"❌ ログアウト失敗: {logout_response.text}")
            
        else:
            print(f"❌ ログイン失敗: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー: サーバーが起動していません")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_full_auth_flow()
