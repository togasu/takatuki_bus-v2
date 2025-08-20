from flask import session, request
import requests
import os
import logging

def check_student_auth():
    """
    studentサービスの認証状態をチェック
    """
    return session.get('student_authenticated', False)

def check_admin_auth():
    """
    adminサービスの認証状態をチェック
    内部的にadminサービスの認証エンドポイントを呼び出す
    """
    try:
        # adminサービスの認証確認エンドポイントに問い合わせ
        admin_host = os.getenv('ADMIN_HOST', 'admin')
        admin_port = os.getenv('ADMIN_PORT', '5000')
        
        # セッションからadmin認証トークンを取得
        admin_token = session.get('admin_token')
        if not admin_token:
            return False
            
        headers = {
            'X-Service-Auth': admin_token,
            'User-Agent': 'student-service-auth-check'
        }
        
        response = requests.get(
            f'http://{admin_host}:{admin_port}/api/auth/check',
            headers=headers,
            timeout=3
        )
        
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Admin auth check failed: {e}")
        return False

def check_driver_auth():
    """
    driverサービスの認証状態をチェック
    内部的にdriverサービスの認証エンドポイントを呼び出す
    """
    try:
        # driverサービスの認証確認エンドポイントに問い合わせ
        driver_host = os.getenv('DRIVER_HOST', 'driver')
        driver_port = os.getenv('DRIVER_PORT', '5000')
        
        # セッションからdriver認証トークンを取得
        driver_token = session.get('driver_token')
        if not driver_token:
            return False
            
        headers = {
            'X-Service-Auth': driver_token,
            'User-Agent': 'student-service-auth-check'
        }
        
        response = requests.get(
            f'http://{driver_host}:{driver_port}/api/auth/check',
            headers=headers,
            timeout=3
        )
        
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Driver auth check failed: {e}")
        return False

def set_student_auth(authenticated=True):
    """
    studentサービスの認証状態を設定
    """
    session['student_authenticated'] = authenticated

def set_admin_auth(token=None):
    """
    adminサービスの認証トークンを設定
    """
    if token:
        session['admin_token'] = token
    else:
        session.pop('admin_token', None)

def set_driver_auth(token=None):
    """
    driverサービスの認証トークンを設定
    """
    if token:
        session['driver_token'] = token
    else:
        session.pop('driver_token', None)
