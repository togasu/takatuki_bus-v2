from flask import Blueprint
from flask_socketio import SocketIO, emit, join_room, leave_room
from ..models.bus import Bus
from ..models.reservation import Reservation
from ..database import db
from datetime import datetime, timedelta

ws_bp = Blueprint('ws', __name__)

# WebSocketイベントハンドラー
def register_socketio_events(socketio):
    
    @socketio.on('connect')
    def handle_connect():
        print('クライアント接続:', flush=True)
        emit('status', {'msg': 'WebSocket接続が確立されました'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('クライアント切断:', flush=True)
    
    @socketio.on('join_bus_updates')
    def handle_join_bus_updates():
        """バス情報のリアルタイム更新ルームに参加"""
        join_room('bus_updates')
        print('バス更新ルームに参加しました', flush=True)
        
        # 現在のバス状況を送信
        current_bus_data = get_current_bus_data()
        emit('bus_data_update', current_bus_data)
    
    @socketio.on('leave_bus_updates')
    def handle_leave_bus_updates():
        """バス情報のリアルタイム更新ルームから離脱"""
        leave_room('bus_updates')
        print('バス更新ルームから離脱しました', flush=True)
    
    @socketio.on('request_bus_data')
    def handle_request_bus_data():
        """現在のバス情報を要求"""
        current_bus_data = get_current_bus_data()
        emit('bus_data_update', current_bus_data)

def get_current_bus_data():
    """現在のバス情報を取得"""
    try:
        # 今日と明日のバス情報を取得
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        # 今日のバスを取得（過去の便は除外）
        current_time = datetime.now()
        buses_today = db.session.query(Bus).filter(
            Bus.departure_time >= current_time,
            db.func.date(Bus.departure_time) == today,
            Bus.status != 2  # キャンセルされていない
        ).order_by(Bus.departure_time).limit(10).all()
        
        # 明日のバスも少し取得
        buses_tomorrow = db.session.query(Bus).filter(
            db.func.date(Bus.departure_time) == tomorrow,
            Bus.status != 2
        ).order_by(Bus.departure_time).limit(5).all()
        
        all_buses = buses_today + buses_tomorrow
        
        bus_data = []
        for bus in all_buses:
            # 予約済み座席数を計算
            reserved_seats = db.session.query(Reservation).filter_by(bus_id=bus.id).count()
            available_seats = bus.seats - reserved_seats
            
            bus_info = {
                "id": bus.id,
                "busid": bus.busid,
                "departure_time": bus.departure_time.strftime('%m/%d %H:%M'),
                "available_seats": available_seats if available_seats >= 0 else 0,
                "total_seats": bus.seats,
                "status": bus.status,
                "ud": bus.ud  # 0: 上り（高槻キャンパス行き）, 1: 下り（高槻駅行き）
            }
            bus_data.append(bus_info)
        
        return bus_data
    
    except Exception as e:
        print(f'バスデータ取得エラー: {e}', flush=True)
        return []

def broadcast_bus_update(socketio):
    """バス情報更新を全クライアントに送信"""
    try:
        current_bus_data = get_current_bus_data()
        socketio.emit('bus_data_update', current_bus_data, room='bus_updates')
        print(f'バス情報更新をブロードキャスト: {len(current_bus_data)}件のバス', flush=True)
    except Exception as e:
        print(f'ブロードキャストエラー: {e}', flush=True)