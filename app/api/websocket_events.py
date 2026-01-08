from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request
from app import socketio
from app.services.jwt_service import verify_token

# Dictionary to store user_id to socket_id mapping
connected_users = {}


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")


@socketio.on('authenticate')
def handle_authenticate(data):
    """Authenticate user and join them to their personal room."""
    token = data.get('token')
    
    if not token:
        emit('error', {'message': 'Missing authentication token'})
        return False
    
    try:
        # Verify JWT token
        payload = verify_token(token)
        user_id = payload.get('user_id')
        
        if not user_id:
            emit('error', {'message': 'Invalid token'})
            return False
        
        # Store the connection
        connected_users[request.sid] = user_id
        
        # Join user to their personal room (for targeted notifications)
        join_room(f'user_{user_id}')
        
        emit('authenticated', {'status': 'success', 'user_id': user_id})
        print(f"User {user_id} authenticated on socket {request.sid}")
        return True
    except Exception as e:
        print(f"Authentication error: {e}")
        emit('error', {'message': 'Authentication failed'})
        return False


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    if request.sid in connected_users:
        user_id = connected_users[request.sid]
        leave_room(f'user_{user_id}')
        del connected_users[request.sid]
        print(f"User {user_id} disconnected")
    else:
        print(f"Unknown client disconnected: {request.sid}")
