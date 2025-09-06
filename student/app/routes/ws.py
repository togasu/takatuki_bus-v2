from flask import request
from app import socketio
from flask_socketio import emit
from app.utils.error_handlers import ErrorLogger
import logging

@socketio.on("connect")
def handle_connect():
    try:
        print(f"[Student Service] Client connected: {request.sid}")
        emit("server_message", {
            "message": "Hello from Student Service WebSocket!"
        })
    except Exception as e:
        ErrorLogger.log_error(e)
        emit("error", {"message": "接続エラーが発生しました"})

@socketio.on("disconnect")
def handle_disconnect():
    try:
        print(f"[Student Service] Client disconnected: {request.sid}")
    except Exception as e:
        ErrorLogger.log_error(e)

@socketio.on("client_message")
def handle_client_message(data):
    try:
        print(f"[Student Service] Received from client: {data}")
        emit("server_message", {
            "message": f"Echo from Student Service: {data}"
        })
    except Exception as e:
        ErrorLogger.log_error(e)
        emit("error", {"message": "メッセージ処理中にエラーが発生しました"})
