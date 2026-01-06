import jwt
import logging
import os
from flask import request, jsonify, g, current_app
from functools import wraps

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"

def get_secret_key():
    """Get SECRET_KEY from Flask app config."""
    return current_app.config.get('SECRET_KEY') or os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            logger.warning("No Authorization header provided")
            return jsonify({'error': 'Unauthorized', 'message': 'Missing Authorization header'}), 401
        
        try:
            # Extract token from "Bearer <token>" format
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                logger.warning(f"Invalid Authorization header format: {auth_header[:20]}...")
                return jsonify({'error': 'Unauthorized', 'message': 'Invalid Authorization header format'}), 401
            
            token = parts[1]
            secret_key = get_secret_key()
            payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
            
            user_id = payload.get('user_id')
            username = payload.get('username')
            
            if not user_id:
                logger.warning("Token missing user_id")
                return jsonify({'error': 'Unauthorized', 'message': 'Invalid token payload'}), 401
            
            g.current_user = {
                'user_id': user_id,
                'username': username
            }
            # Also set on request for backwards compatibility
            request.user_id = user_id
            request.username = username
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            return jsonify({'error': 'Unauthorized', 'message': 'Token expired'}), 401
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Authorization error: {str(e)}", exc_info=True)
            return jsonify({'error': 'Unauthorized', 'message': 'Authorization failed'}), 401
    return decorated

def require_auth(f):
    """Alias for auth_required for backwards compatibility"""
    return auth_required(f)