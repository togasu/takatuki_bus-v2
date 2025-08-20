from flask import Blueprint, render_template, redirect, url_for, session
from app.auth_checker import check_student_auth, check_admin_auth, check_driver_auth

bp = Blueprint("top", __name__)

@bp.route("/", methods=["GET"])
def top():
    # 1. studentの認証が完了していればtop.htmlを表示
    if check_student_auth():
        # セッションから学生情報を取得
        student_id = session.get('student_id', '')
        student_name = session.get('student_name', 'ゲスト')
        
        # テンプレートに必要なデータを準備（実際の実装では適切なデータを取得）
        context = {
            'name': student_id,
            'user_full_name': student_name,
            'len_count': 1,  # デモデータ
            'current_time': [],
            'cur_bus_id': [],
            'current': [],
            'i': 0,
            'departure_time': [],
            'bus_id': [],
            'seat_number': []
        }
        return render_template("top.html", **context)
    
    # 2. adminの認証が完了していれば/admin/にリダイレクト
    if check_admin_auth():
        return redirect("/admin/")
    
    # 3. driverの認証が完了していれば/driver/にリダイレクト
    if check_driver_auth():
        return redirect("/driver/")
    
    # 4. いずれの認証も完了していなければauth.htmlを表示
    return render_template("auth.html")
