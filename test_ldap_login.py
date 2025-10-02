#!/usr/bin/env python3
"""
LDAPログインのテストスクリプト
"""

import requests
import sys

def test_ldap_login():
    """LDAPログインをテストする"""
    
    # テスト用の認証情報（実際の認証情報ではありません）
    test_data = {
        'username': 'k230092',  # テスト用k番号
        'password': 'test_password'  # テスト用パスワード
    }
    
    try:
        print("studentサービスのLDAPログインをテスト中...")
        
        # ログインエンドポイントにPOST
        response = requests.post(
            'https://localhost/login',
            data=test_data,
            verify=False,  # 自己署名証明書のため
            allow_redirects=False,
            timeout=10
        )
        
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンスヘッダー: {dict(response.headers)}")
        
        if response.status_code == 200:
            # ログインページが再表示される場合（認証失敗）
            if 'maintenance' in response.text.lower():
                print("❌ maintenance画面が表示されています")
                return False
            else:
                print("✅ ログインページが正常に表示されています（認証失敗は想定通り）")
                return True
        elif response.status_code == 302:
            # リダイレクトされる場合（認証成功またはエラーページ）
            location = response.headers.get('Location', '')
            print(f"リダイレクト先: {location}")
            if 'maintenance' in location.lower():
                print("❌ maintenance画面にリダイレクトされています")
                return False
            else:
                print("✅ 正常なリダイレクトです")
                return True
        else:
            print(f"⚠️ 予期しないステータスコード: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ テスト中にエラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    success = test_ldap_login()
    sys.exit(0 if success else 1)
