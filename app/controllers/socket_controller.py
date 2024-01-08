from flask import request
from app import socketio

@socketio.on('connect')
def onConnect():
    userid = request.sid
    socketio.emit('user_id', {'user_id': userid})