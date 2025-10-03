import re
from datetime import datetime, timedelta
from ldap3 import Server, Connection, ALL
from flask import current_app
from ..config import LDAP_SERVER, LDAP_USER_DN_TEMPLATE, LDAP_BASE_DN

def extract_student_id_from_gecos(gecos_value):
    """gecosの値から学籍番号に当たる部分を抜き出す処理"""
    student_id_pattern = re.compile(r'(\d+)')
    match = student_id_pattern.search(gecos_value)
    number_part = match.group(1)
    print(f"number_part={number_part}")
    if len(number_part) >= 9:
        student_id = number_part[-6:]
    else:
        student_id = number_part
        # 院生は8桁で3,4桁が10ならM，20ならD
    return student_id if match else None

def extract_user_full_name_from_gecos(gecos_value):
    """gecosの値から名前に当たる部分を抜き出す処理"""
    name_pattern = r'\b[A-Za-z]+\b'
    matches = re.findall(name_pattern, gecos_value)
    user_full_name = matches[0] + ' ' + matches[1]
    return user_full_name 

def user_password_exist(username, password):
    """LDAP認証"""
    exist = False
    user_full_name = "Nanashi"
    student_id = None

    # 実際のLDAP認証
    user_dn = LDAP_USER_DN_TEMPLATE.format(username=username)

    s = Server(LDAP_SERVER, get_info=ALL)
    c = Connection(s, user=user_dn, password=password, check_names=True, lazy=False)
    
    try:
        ret = c.bind()
        if ret:
            exist = True
            search_filter = f'(uid={username})' 
            c.search(LDAP_BASE_DN, search_filter, attributes=['gecos'])  # gecos属性のみを取得
            if c.entries:
                entry = c.entries[0]
                gecos = str(entry.gecos)
                print(f'gecos={gecos}')
                # gecosからstudent_idを抜き出す
                student_id = extract_student_id_from_gecos(gecos)
                print(f'student_id={student_id}')
                user_full_name = extract_user_full_name_from_gecos(gecos) 
                print(f'user_full_name={user_full_name}')
            else:
                print("No LDAP entries found for user")
                exist = False
        else:
            exist = False
    except Exception as e:
        print(f"エラー: {e}")
        exist = False
    finally:
        c.unbind()

    return exist, student_id, user_full_name

def add_token_str(k_number, student_id):
    """トークンを生成して保存（Redisベース）"""
    token_manager = getattr(current_app, 'token_manager', None)
    if token_manager:
        token = token_manager.create_session(k_number, student_id)
        if token:
            return token
        else:
            print("Failed to create session in Redis")
            return None
    else:
        print("Redis token manager not available")
        return None

def add_admin_token_str(username, admin_info):
    """adminユーザー用のトークンを生成して保存（Redisベース）"""
    token_manager = getattr(current_app, 'token_manager', None)
    if token_manager:
        # adminユーザー用の特別なセッションデータ
        session_data = {
            'username': username,
            'user_id': admin_info.get('user_id'),
            'role': 'admin',
            'email': admin_info.get('email'),
            'type': 'admin_user'  # 管理者ユーザーとして識別
        }
        token = token_manager.create_admin_session(username, session_data)
        if token:
            return token
        else:
            print("Failed to create admin session in Redis")
            return None
    else:
        print("Redis token manager not available")
        return None

def check_session(personal_token):
    """セッションチェック（Redisベース）"""
    token_manager = getattr(current_app, 'token_manager', None)
    if token_manager:
        return token_manager.check_session(personal_token)
    else:
        print("Redis token manager not available")
        return {'flag': False}
