import re
from ldap3 import Server, Connection, ALL


def check_ldap_connection():
    """
    LDAP サーバーへの接続をテストする
    
    Returns:
        bool: 接続成功の場合True、失敗の場合False
    """
    try:
        server_uri = 'ldap://tcs11.edu.kutc.kansai-u.ac.jp'
        s = Server(server_uri, get_info=ALL)
        
        # 匿名接続でサーバーの応答をテスト
        c = Connection(s, auto_bind=True)
        c.unbind()
        return True
    except Exception as e:
        print(f"LDAP接続テストエラー: {e}")
        return False


def extract_student_id_from_gecos(gecos_value):
    """gecosの値から学籍番号に当たる部分を抜き出す処理"""
    student_id_pattern = re.compile(r'(\d+)')
    match = student_id_pattern.search(gecos_value)
    if not match:
        return None
        
    number_part = match.group(1)
    print(f"number_part={number_part}")
    
    if len(number_part) >= 9:
        student_id = number_part[-6:]
    else:
        student_id = number_part
        # 院生は8桁で3,4桁が10ならM，20ならD
    
    return student_id


def extract_user_full_name_from_gecos(gecos_value):
    """gecosの値から名前に当たる部分を抜き出す処理"""
    name_pattern = r'\b[A-Za-z]+\b'
    matches = re.findall(name_pattern, gecos_value)
    
    if len(matches) >= 2:
        user_full_name = matches[0] + ' ' + matches[1]
    elif len(matches) == 1:
        user_full_name = matches[0]
    else:
        user_full_name = "Unknown"
    
    return user_full_name


def authenticate_ldap_user(username, password):
    """
    LDAP認証を行い、認証情報を返す
    
    Args:
        username (str): ユーザー名
        password (str): パスワード
    
    Returns:
        tuple: (認証成功フラグ, 学籍番号, フルネーム)
    """
    exist = False
    user_full_name = "Nanashi"
    student_id = None

    # LDAP で認証
    server_uri = 'ldap://tcs11.edu.kutc.kansai-u.ac.jp'
    user_dn = f'uid={username},ou=People,dc=kutc,dc=kansai-u,dc=ac,dc=jp'

    try:
        s = Server(server_uri, get_info=ALL, connect_timeout=5)
        c = Connection(s, user=user_dn, password=password, check_names=True, lazy=False, 
                      read_only=True, receive_timeout=10)
        
        ret = c.bind()
        if ret:
            exist = True
            search_base = 'dc=kutc,dc=kansai-u,dc=ac,dc=jp'
            search_filter = f'(uid={username})'
            c.search(search_base, search_filter, attributes=['gecos'])  # gecos属性のみを取得
            
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
                exist = False
        else:
            exist = False
            
    except Exception as e:
        print(f"LDAP認証エラー: {e}")
        exist = False
    finally:
        try:
            c.unbind()
        except:
            pass

    return exist, student_id, user_full_name


def check_ldap_connection():
    """
    LDAPサーバーへの接続確認を行う
    Returns:
        bool: 接続可能な場合True、不可能な場合False
    """
    server_uri = 'ldap://tcs11.edu.kutc.kansai-u.ac.jp'
    
    try:
        # 匿名接続でサーバーの生存確認
        s = Server(server_uri, get_info=ALL, connect_timeout=3)
        c = Connection(s, auto_bind=True, receive_timeout=5)
        c.unbind()
        return True
    except Exception as e:
        print(f"LDAP接続エラー: {e}")
        return False
