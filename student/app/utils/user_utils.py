"""
ユーザー管理関連のユーティリティ関数
"""

from flask import current_app
from ..models.user import User, LastSemester_user
from ..database import db

def check_user_registration(student_id):
    """
    外部APIの check_user 機能を内部で実装
    
    Args:
        student_id (str): 学生ID
        
    Returns:
        tuple: (status_code, message)
            - 200: 利用者登録済み
            - 404: Spring userのみ登録
            - 400: 利用者登録未済
    """
    try:
        # 通常のユーザー（秋学期ユーザー）をチェック
        user = db.session.query(User).filter(User.student_id == student_id).first()
        
        if user is None:
            # 前学期ユーザーをチェック
            last_semester_user = db.session.query(LastSemester_user).filter(LastSemester_user.student_id == student_id).first()
            
            if last_semester_user is None:
                # どちらにも登録されていない
                return 400, '利用者登録が済んでいません.キャンパスオフィスで利用者登録をしてください'
            else:
                # 前学期ユーザーのみ登録
                return 404, 'you are not fall user'
        
        # 通常のユーザーとして登録済み
        return 200, '利用者登録が済んでいます'
        
    except Exception as e:
        current_app.logger.error(f"ユーザー登録確認エラー: {e}")
        # データベースエラーの場合は登録未済として扱う
        return 400, 'データベースエラー: 利用者登録確認ができませんでした'
