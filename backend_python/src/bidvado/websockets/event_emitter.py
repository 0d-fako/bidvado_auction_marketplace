from typing import Dict, Any
from flask_socketio import SocketIO


class EventEmitter:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio

    def emit(self, event_name: str, data: Dict[str, Any], room: str = None):
        if room:
            self.socketio.emit(event_name, data, room=room)
        else:
            self.socketio.emit(event_name, data)

    def join_room(self, room: str, sid: str):
        from flask_socketio import join_room
        join_room(room, sid=sid)

    def leave_room(self, room: str, sid: str):
        from flask_socketio import leave_room
        leave_room(room, sid=sid)