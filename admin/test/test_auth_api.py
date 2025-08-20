#!/usr/bin/env python3
"""
テストユーザーでの認証をテストするスクリプト
"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost"

def test_login(username, password):
    """ログインをテスト"""
    login_url = f"{BASE_URL}/admin/api/auth/login"
    
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(login_url, json=data)
        
        print(f"\n=== {username} でのログインテスト ===")
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ログイン成功!")
            print(f"トークン: {result.get('token', 'なし')}")
            print(f"ユーザー情報: {result.get('user', {})}")
            return result.get('token')
        else:
            print(f"❌ ログイン失敗: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 接続エラー: サーバーが起動していません ({login_url})")
        return None
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

def test_permissions(token, username):
    """権限をテスト"""
    if not token:
        return
    
    print(f"\n=== {username} の権限テスト ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # ユーザー一覧取得をテスト
    users_url = f"{BASE_URL}/admin/api/users"
    try:
        response = requests.get(users_url, headers=headers)
        print(f"ユーザー一覧取得: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            print(f"  取得ユーザー数: {len(users)}")
        else:
            print(f"  エラー: {response.text}")
    except Exception as e:
        print(f"  エラー: {e}")
    
    # 権限一覧取得をテスト
    permissions_url = f"{BASE_URL}/admin/api/permissions"
    try:
        response = requests.get(permissions_url, headers=headers)
        print(f"権限一覧取得: {response.status_code}")
        if response.status_code == 200:
            permissions = response.json()
            print(f"  取得権限数: {len(permissions)}")
        else:
            print(f"  エラー: {response.text}")
    except Exception as e:
        print(f"  エラー: {e}")

def test_logout(token):
    """ログアウトをテスト"""
    if not token:
        return
    
    logout_url = f"{BASE_URL}/admin/api/auth/logout"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(logout_url, headers=headers)
        print(f"\nログアウト: {response.status_code}")
        if response.status_code == 200:
            print("✅ ログアウト成功!")
        else:
            print(f"❌ ログアウト失敗: {response.text}")
    except Exception as e:
        print(f"❌ ログアウトエラー: {e}")

def main():
    """メイン処理"""
    print("=" * 50)
    print("テストユーザー認証テスト")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # テストユーザーのログイン情報
    test_users = [
        {"username": "admin_test", "password": "admin123", "role": "admin"},
        {"username": "normal_test", "password": "normal123", "role": "normal"},
        {"username": "guest_test", "password": "guest123", "role": "guest"}
    ]
    
    for user_info in test_users:
        username = user_info["username"]
        password = user_info["password"]
        
        # ログインテスト
        token = test_login(username, password)
        
        # 権限テスト
        test_permissions(token, username)
        
        # ログアウトテスト
        test_logout(token)
        
        print("-" * 30)
    
    print("\nテスト完了!")

if __name__ == "__main__":
    main()
