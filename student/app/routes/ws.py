from flask import request
from app import socketio
from flask_socketio import emit

@socketio.on("connect")
def handle_connect():
    print(f"[Service 1] Client connected: {request.sid}")
    emit("server_message", {
        "message": "Hello from Service 1 WebSocket!"
    })

@socketio.on("disconnect")
def handle_disconnect():
    print(f"[Service 1] Client disconnected: {request.sid}")

@socketio.on("client_message")
def handle_client_message(data):
    print(f"[Service 1] Received from client: {data}")
    emit("server_message", {
        "message": f"Echo from Service 1: {data}"
    })
