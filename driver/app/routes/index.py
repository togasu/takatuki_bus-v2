from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.utils.session_manager import session_manager

bp = Blueprint("index", __name__)

@bp.route("/", methods=["GET"])
def index():
    """ドライバーサービスのメインページ"""
    # バス運行情報の取得（模擬データ）
    next_bus = "15:30発 - 大学前行き"
    following_bus = "16:00発 - 駅前行き"
    message = ""  # エラーメッセージがある場合に使用
    
    return render_template('top.html', 
                         message=message, 
                         firstbus=next_bus, 
                         secoundbus=following_bus)

@bp.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "service": "Driver",
        "status": "healthy",
        "message": "Driver service is running"
    }

@bp.route("/api/status", methods=["GET"])
def api_status():
    """API用のステータスエンドポイント"""
    return {
        "service": "Driver Service",
        "status": "running",
        "message": "タカツキバス ドライバーサービスが正常に動作しています",
        "endpoints": {
            "health": "/health",
            "api": "/api/*",
            "websocket": "/socket.io"
        }
    }
