from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from typing import Dict, Any


class WebSocketHandler:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self._setup_handlers()

    def _setup_handlers(self):

        @self.socketio.on('connect')
        def handle_connect():
            sid = request.sid if hasattr(request, 'sid') else 'unknown'
            print(f"Client connected: {sid}")

        @self.socketio.on('disconnect')
        def handle_disconnect():
            sid = request.sid if hasattr(request, 'sid') else 'unknown'
            print(f"Client disconnected: {sid}")

        @self.socketio.on('join')
        def handle_join(data):
            if 'room' in data:
                room = data['room']
                sid = request.sid if hasattr(request, 'sid') else None
                if sid:
                    join_room(room, sid=sid)
                    print(f"Client {sid} joined room: {room}")
                    emit('joined', {'room': room})
                else:
                    emit('error', {'message': 'Could not join room'})

        @self.socketio.on('leave')
        def handle_leave(data):
            if 'room' in data:
                room = data['room']
                sid = request.sid if hasattr(request, 'sid') else None
                if sid:
                    leave_room(room, sid=sid)
                    print(f"Client {sid} left room: {room}")
                    emit('left', {'room': room})
                else:
                    emit('error', {'message': 'Could not leave room'})

    def emit(self, event: str, data: Dict[str, Any], room=None):
        if room:
            self.socketio.emit(event, data, room=room)
        else:
            self.socketio.emit(event, data)

    def emit_to_user(self, user_id: str, event: str, data: Dict[str, Any]):
        self.emit(event, data, room=f"user_{user_id}")

    def emit_to_auction(self, auction_id: str, event: str, data: Dict[str, Any]):
        self.emit(event, data, room=f"auction_{auction_id}")