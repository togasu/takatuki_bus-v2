from flask import Blueprint, render_template, session, request, jsonify, redirect, url_for
from app.utils.auth_utils import SessionManager

bp = Blueprint("index", __name__)
session_manager = SessionManager()

@bp.route("/", methods=["GET"])
def index():
    """管理者ダッシュボード"""
    # APIリクエストの場合はJSONレスポンスを返す
    if request.headers.get('Content-Type') == 'application/json' or request.headers.get('Accept') == 'application/json':
        return {
            "service": "Admin",
            "message": "HTTP route works!"
        }
    
    # ブラウザからのアクセスの場合は管理画面を表示
    return render_template("admin_dashboard.html")

@bp.route("/logout", methods=["GET", "POST"])
def logout():
    """ログアウト処理"""
    # セッション情報があれば削除
    admin_token = session.get('admin_token')
    if admin_token:
        session_manager.delete_session(admin_token)
    
    session.clear()
    return redirect("https://localhost/")
