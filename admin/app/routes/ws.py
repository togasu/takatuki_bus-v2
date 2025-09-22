from flask import request
from app import socketio
from flask_socketio import emit, join_room, leave_room
from app.utils.error_handlers import ErrorLogger
import logging
import threading
import time
try:
    import numpy as np
except ImportError:
    # numpyがない場合は標準のrandomを使用
    import random
    
    class MockNumpy:
        def random(self):
            class RandomMock:
                def randint(self, low, high):
                    return random.randint(low, high)
                
                def uniform(self, low, high):
                    return random.uniform(low, high)
            return RandomMock()
    
    np = MockNumpy()

from datetime import datetime

# 統計情報ルーム管理
statistics_clients = set()

@socketio.on("connect")
def handle_connect():
    try:
        client_id = request.sid
        print(f"[Admin Service] Client connected: {client_id}")
        emit("server_message", {
            "message": "Hello from Admin Service WebSocket!"
        })
    except Exception as e:
        ErrorLogger.log_error(e)
        emit("error", {"message": "接続エラーが発生しました"})

@socketio.on("disconnect")
def handle_disconnect():
    try:
        client_id = request.sid
        print(f"[Admin Service] Client disconnected: {client_id}")
        # 統計情報ルームから除外
        if client_id in statistics_clients:
            statistics_clients.remove(client_id)
    except Exception as e:
        ErrorLogger.log_error(e)

@socketio.on("client_message")
def handle_client_message(data):
    try:
        print(f"[Admin Service] Received from client: {data}")
        emit("server_message", {
            "message": f"Echo from Admin Service: {data}"
        })
    except Exception as e:
        ErrorLogger.log_error(e)
        emit("error", {"message": "メッセージ処理中にエラーが発生しました"})

@socketio.on("join_statistics")
def handle_join_statistics():
    """統計情報のリアルタイム更新ルームに参加"""
    try:
        client_id = request.sid
        statistics_clients.add(client_id)
        join_room("statistics")
        print(f"[Admin Service] Client {client_id} joined statistics room")
        emit("server_message", {
            "message": "統計情報のリアルタイム更新に参加しました"
        })
    except Exception as e:
        ErrorLogger.log_error(e)
        emit("error", {"message": "統計情報ルームへの参加に失敗しました"})

@socketio.on("leave_statistics")
def handle_leave_statistics():
    """統計情報のリアルタイム更新ルームから離脱"""
    try:
        client_id = request.sid
        if client_id in statistics_clients:
            statistics_clients.remove(client_id)
        leave_room("statistics")
        print(f"[Admin Service] Client {client_id} left statistics room")
        emit("server_message", {
            "message": "統計情報のリアルタイム更新から離脱しました"
        })
    except Exception as e:
        ErrorLogger.log_error(e)
        emit("error", {"message": "統計情報ルームからの離脱に失敗しました"})

def start_statistics_broadcaster():
    """統計情報のリアルタイム配信を開始"""
    def broadcast_statistics():
        while True:
            try:
                if statistics_clients:
                    # リアルタイムデータを生成（サンプル）
                    current_time = datetime.now()
                    
                    # numpyかrandomかを判別して使用
                    if hasattr(np, 'random'):
                        # numpy使用
                        random_gen = np.random
                    else:
                        # mockクラス使用
                        random_gen = np.random()
                    
                    realtime_data = {
                        'timestamp': current_time.isoformat(),
                        'active_connections': len(statistics_clients) + random_gen.randint(5, 25),
                        'memory_usage': random_gen.uniform(30, 80),
                        'cpu_usage': random_gen.uniform(10, 60),
                        'request_per_minute': random_gen.randint(50, 200)
                    }
                    
                    # 統計情報ルームにブロードキャスト
                    socketio.emit('statistics_update', realtime_data, to='statistics')
                
                # 5秒間隔で更新
                time.sleep(5)
                
            except Exception as e:
                ErrorLogger.log_error(e)
                time.sleep(5)
    
    # バックグラウンドスレッドで実行
    thread = threading.Thread(target=broadcast_statistics, daemon=True)
    thread.start()
    print("[Admin Service] Statistics broadcaster started")
