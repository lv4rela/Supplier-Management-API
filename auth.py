from flask import request, jsonify, g
from functools import wraps
import jwt
from datetime import datetime, timedelta
from config import Config
from models import User

def generate_jwt(user):
    token = jwt.encode({
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    }, Config.JWT_SECRET_KEY, algorithm='HS256')
    return token

def verify_jwt(token):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return jsonify({"message": "Authorization header is missing"}), 401
        
        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return jsonify({"message": "Invalid authorization header format"}), 401
        
        token = parts[1]
        user_payload = verify_jwt(token)
        if user_payload is None:
            return jsonify({"message": "Invalid or expired token"}), 401
        
        g.user = user_payload
        return f(*args, **kwargs)
    
    return decorated
