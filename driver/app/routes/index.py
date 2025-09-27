from flask import Blueprint, render_template, request, redirect, url_for
from app.utils.session_manager import session_manager

bp = Blueprint("index", __name__)

@bp.route("/", methods=["GET"])
def index():
    """メインページへのリダイレクト"""
    return redirect(url_for('main.index'))

@bp.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "service": "Driver",
        "status": "healthy",
        "message": "Driver service is running"
    }
