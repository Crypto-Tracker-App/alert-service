import os
import requests
from flask import request, jsonify, g
from functools import wraps

AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL', 'http://auth-service:5000')

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth:
            return jsonify({'error': 'Unauthorized'}), 401
        try:
            r = requests.get(f"{AUTH_SERVICE_URL}/api/auth/verify-session", headers={'Authorization': auth}, timeout=3)
            if r.status_code == 200:
                g.current_user = r.json().get('user')
                return f(*args, **kwargs)
        except Exception:
            pass
        return jsonify({'error': 'Unauthorized'}), 401
    return decorated

def require_auth(f):
    return auth_required(f)