from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.database import db
from app.models.user import User
from app.authorization import require_permission, require_role
import re

bp = Blueprint('admin_create', __name__)

@bp.route('/create', methods=['GET'])
@require_permission("admin_user", "create")
def admin_create_form():
    """管理者アカウント作成フォームを表示"""
    return render_template('admin_create.html')

@bp.route('/create', methods=['POST'])
@require_permission("admin_user", "create")
def admin_create_submit():
    """管理者アカウント作成処理（フォーム用）"""
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    role = request.form.get('role', 'admin')
    is_active = request.form.get('is_active') == 'on'

    # バリデーション
    errors = []
    
    if not username:
        errors.append('ユーザー名は必須です')
    elif len(username) < 3:
        errors.append('ユーザー名は3文字以上で入力してください')
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append('ユーザー名は英数字とアンダースコアのみ使用できます')
    
    if not email:
        errors.append('メールアドレスは必須です')
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors.append('有効なメールアドレスを入力してください')
    
    if not password:
        errors.append('パスワードは必須です')
    elif len(password) < 8:
        errors.append('パスワードは8文字以上で入力してください')
    
    if password != confirm_password:
        errors.append('パスワードが一致しません')
    
    if role not in ['guest', 'normal', 'admin']:
        errors.append('無効な権限レベルです')
    
    # 既存ユーザーの重複チェック
    if User.query.filter_by(username=username).first():
        errors.append('このユーザー名は既に使用されています')
    
    if User.query.filter_by(email=email).first():
        errors.append('このメールアドレスは既に使用されています')
    
    if errors:
        for error in errors:
            flash(error, 'error')
        return render_template('admin_create.html', 
                             username=username, 
                             email=email, 
                             role=role, 
                             is_active=is_active)
    
    try:
        # 新しい管理者ユーザーを作成
        user = User(
            username=username,
            email=email,
            role=role,
            is_active=is_active
        )
        
        # パスワードをハッシュ化して設定
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'管理者アカウント「{username}」を正常に作成しました', 'success')
        return redirect(url_for('index.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'エラーが発生しました: {str(e)}', 'error')
        return render_template('admin_create.html',
                             username=username,
                             email=email,
                             role=role,
                             is_active=is_active)

@bp.route('/api/create', methods=['POST'])
@require_permission("admin_user", "create")
def api_admin_create():
    """管理者アカウント作成API"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "データが提供されていません"}), 400
    
    # 必須フィールドのチェック
    required_fields = ["username", "email", "password"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return jsonify({
            "error": "必須フィールドが不足しています",
            "missing_fields": missing_fields
        }), 400
    
    username = data["username"].strip()
    email = data["email"].strip()
    password = data["password"]
    role = data.get("role", "admin")
    is_active = data.get("is_active", True)
    
    # バリデーション
    validation_errors = []
    
    if len(username) < 3:
        validation_errors.append("ユーザー名は3文字以上で入力してください")
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        validation_errors.append("ユーザー名は英数字とアンダースコアのみ使用できます")
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        validation_errors.append("有効なメールアドレスを入力してください")
    
    if len(password) < 8:
        validation_errors.append("パスワードは8文字以上で入力してください")
    
    if role not in ['guest', 'normal', 'admin']:
        validation_errors.append("無効な権限レベルです")
    
    # 既存ユーザーの重複チェック
    if User.query.filter_by(username=username).first():
        validation_errors.append("このユーザー名は既に使用されています")
    
    if User.query.filter_by(email=email).first():
        validation_errors.append("このメールアドレスは既に使用されています")
    
    if validation_errors:
        return jsonify({
            "error": "バリデーションエラー",
            "validation_errors": validation_errors
        }), 400
    
    try:
        # 新しい管理者ユーザーを作成
        user = User(
            username=username,
            email=email,
            role=role,
            is_active=is_active
        )
        
        # パスワードをハッシュ化して設定
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "message": "管理者アカウントを正常に作成しました",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "アカウント作成中にエラーが発生しました",
            "details": str(e)
        }), 500