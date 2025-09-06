from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth_checker import set_student_auth, set_admin_auth, set_driver_auth
from app.utils.decorators import safe_route
from app.utils.error_handlers import ErrorLogger
import requests
import os
import logging

bp = Blueprint("auth", __name__)

@bp.route("/auth", methods=["GET"])
@safe_route
def auth():
    return render_template("auth.html")

@bp.route("/login", methods=["POST"])
@safe_route
def login():
    """統一ログインエンドポイント - バックエンドで認証判定"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    logging.info(f"Login attempt for username: {username}")
    
    if not username or not password:
        flash("ユーザー名とパスワードを入力してください")
        return render_template("auth.html")
    
    # 1. 学生認証を試行
    logging.info("Trying student authentication...")
    if try_student_auth(username, password):
        set_student_auth(True)
        logging.info("Student authentication successful")
        return redirect("/")
    
    # 2. 管理者認証を試行
    logging.info("Trying admin authentication...")
    admin_token = try_admin_auth(username, password)
    if admin_token:
        logging.info("Admin authentication successful")
        set_admin_auth(admin_token)
        return redirect("/admin/")
    
    # 3. ドライバー認証を試行
    logging.info("Trying driver authentication...")
    driver_token = try_driver_auth(username, password)
    if driver_token:
        logging.info("Driver authentication successful")
        set_driver_auth(driver_token)
        return redirect("/driver/")
    
    # 全ての認証に失敗
    logging.info("All authentication attempts failed")
    flash("ログインに失敗しました。ユーザー名またはパスワードが正しくありません。")
    return render_template("auth.html")

def try_student_auth(username, password):
    """学生認証を試行"""
    try:
        # 学生データベースから認証を確認
        from app.models.student import Student
        
        # 学生IDで学生を検索
        student = Student.query.filter_by(student_id=username).first()
        
        if student and student.check_password(password):
            # セッションに学生情報を保存
            session['student_id'] = student.student_id
            session['student_name'] = student.name
            return True
        
        return False
    except Exception as e:
        logging.error(f"Student authentication error: {e}")
        return False

def try_admin_auth(username, password):
    """管理者認証を試行"""
    try:
        admin_host = os.getenv('ADMIN_HOST', 'admin')
        admin_port = os.getenv('ADMIN_PORT', '5000')
        
        auth_data = {
            'username': username,
            'password': password
        }
        
        response = requests.post(
            f'http://{admin_host}:{admin_port}/api/auth/login',
            json=auth_data,
            timeout=5
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('token')
        
        return None
        
    except Exception as e:
        logging.error(f"Admin authentication error: {e}")
        return None

def try_driver_auth(username, password):
    """ドライバー認証を試行"""
    try:
        driver_host = os.getenv('DRIVER_HOST', 'driver')
        driver_port = os.getenv('DRIVER_PORT', '5000')
        
        auth_data = {
            'username': username,
            'password': password
        }
        
        response = requests.post(
            f'http://{driver_host}:{driver_port}/api/auth/login',
            json=auth_data,
            timeout=5
        )
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('token')
        
        return None
        
    except Exception as e:
        logging.error(f"Driver authentication error: {e}")
        return None

@bp.route("/logout", methods=["GET", "POST"])
def logout():
    """ログアウト処理"""
    # 全ての認証状態をクリア
    session.clear()
    return redirect("/")