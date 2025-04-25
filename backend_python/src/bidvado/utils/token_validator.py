from flask import request, jsonify
from functools import wraps
from src.bidvado.services.auth_service_impl import AuthService
from src.bidvado.data.repositories.user_repository import UserRepository

auth_service = AuthService(UserRepository())

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            valid, user_id = auth_service.validate_token(token)
            if not valid:
                return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return jsonify({"error": str(e)}), 401
        return f(user_id, *args, **kwargs)
    return decorated_function