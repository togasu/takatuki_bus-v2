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
    
    # クエリパラメータからメッセージを取得
    message = request.args.get('message', '')
    
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
        
        logger.info(f"Bus number: {bus_number}, Retrieved buses count: {len(buses)}")
        logger.info(f"Buses data: {buses}")
        
        firstbus = None
        secondbus = None
        
        if len(buses) > 0:
            bus_data = buses[0]
            departure_dt = datetime.fromisoformat(bus_data['departure_time'])
            firstbus = {
                'destination': yukisaki(bus_data['ud']),
                'date': departure_dt.strftime('%m/%d'),
                'time': departure_dt.strftime('%H:%M'),
                'bus_number': bus_data['busid']
            }
        
        if len(buses) > 1:
            bus_data = buses[1]
            departure_dt = datetime.fromisoformat(bus_data['departure_time'])
            secondbus = {
                'destination': yukisaki(bus_data['ud']),
                'date': departure_dt.strftime('%m/%d'),
                'time': departure_dt.strftime('%H:%M'),
                'bus_number': bus_data['busid']
            }
        
        return render_template('top.html', 
                             message=message, 
                             firstbus=firstbus, 
                             secondbus=secondbus)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        # エラーの場合はNoneを返す
        return render_template('top.html', 
                             message="バス情報の取得中にエラーが発生しました", 
                             firstbus=None, 
                             secondbus=None)

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
