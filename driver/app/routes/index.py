from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app.utils.session_manager import session_manager
from app.utils.helper_functions import get_authenticated_user, yukisaki
from app.models import Driver
from app.database import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("index", __name__)

@bp.route("/", methods=["GET"])
def index():
    """ドライバーサービスのメインページ"""
    # 認証チェック
    user = get_authenticated_user()
    logger.info(f"Index route accessed - Authenticated user: {user}")
    
    if not user:
        # 未認証の場合はログインページにリダイレクト
        return redirect(url_for('main.login'))
    
    # 認証済みの場合はtopページを表示
    try:
        # ドライバー情報を取得
        driver_obj = db.session.query(Driver).filter_by(username=user).first()
        if not driver_obj:
            logger.error(f"Driver not found: {user}")
            return redirect(url_for('main.login'))
        
        # バス番号を取得
        bus_number = driver_obj.number
        
        # バス運行情報の取得（実際のAPIから）
        from app.utils.student_api_client import get_student_client
        client = get_student_client()
        buses = client.get_upcoming_buses_by_number(bus_number, limit=2)
        
        firstbus = "バスがありません"
        secondbus = "バスがありません"
        
        if len(buses) > 0:
            bus_data = buses[0]
            departure_dt = datetime.fromisoformat(bus_data['departure_time'])
            ud = yukisaki(bus_data['ud'])
            firstbus = f"行き先|{ud}  出発時刻|{departure_dt.strftime('%m/%d %H:%M')} {bus_data['busid']}号車"
        
        if len(buses) > 1:
            bus_data = buses[1]
            departure_dt = datetime.fromisoformat(bus_data['departure_time'])
            ud = yukisaki(bus_data['ud'])
            secondbus = f"行き先|{ud}  出発時刻|{departure_dt.strftime('%m/%d %H:%M')} {bus_data['busid']}号車"
        
        return render_template('top.html', 
                             message="", 
                             firstbus=firstbus, 
                             secoundbus=secondbus)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        # エラーの場合は模擬データを表示
        return render_template('top.html', 
                             message="バス情報の取得中にエラーが発生しました", 
                             firstbus="情報取得中...", 
                             secoundbus="情報取得中...")

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
