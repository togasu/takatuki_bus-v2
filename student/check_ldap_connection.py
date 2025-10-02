#!/usr/bin/env python3
"""
LDAP接続確認スクリプト
studentサービスがLDAPサーバーに接続できるかを確認します。
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import LDAPException

def check_ldap_connection():
    """LDAPサーバーへの接続テスト"""
    try:
        # LDAP サーバーの設定
        server_uri = 'ldap://tcs11.edu.kutc.kansai-u.ac.jp'
        
        # サーバーへの接続テスト（匿名接続）
        server = Server(server_uri, get_info=ALL, connect_timeout=10)
        connection = Connection(server, auto_bind=True)
        
        if connection.bound:
            print("ldapサーバと接続されています")
            connection.unbind()
            return True
        else:
            print("ldapサーバとの接続ができませんでした")
            return False
            
    except LDAPException as e:
        print(f"ldapサーバとの接続ができませんでした (LDAP Error: {e})")
        return False
    except Exception as e:
        print(f"ldapサーバとの接続ができませんでした (Error: {e})")
        return False

if __name__ == "__main__":
    success = check_ldap_connection()
    sys.exit(0 if success else 1)
