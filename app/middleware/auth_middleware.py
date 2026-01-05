import os
import jwt
import logging
from flask import request, jsonify, g
from functools import wraps

logger = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Unauthorized'}), 401
        
        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            g.current_user = {
                'user_id': payload.get('user_id'),
                'username': payload.get('username')
            }
            # Also set on request for backwards compatibility
            request.user_id = payload.get('user_id')
            request.username = payload.get('username')
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            logger.error("Invalid token")
            return jsonify({'error': 'Invalid token'}), 401
        except Exception:
            return jsonify({'error': 'Unauthorized'}), 401
    return decorated

def require_auth(f):
    """Alias for auth_required for backwards compatibility"""
    return auth_required(f)