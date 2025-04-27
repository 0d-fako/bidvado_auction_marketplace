import jwt
import os
import functools
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, Callable, Any
from flask import request, jsonify

from ..data.repositories.user_repository import UserRepository
from ..exceptions.auth_exceptions import (
    InvalidTokenException,
    ExpiredTokenException,
    TokenVerificationException,
    UnauthorizedAccessException
)


class JWTManager:

    def __init__(self, user_repository: UserRepository):
        self.SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "bidvado_development_key")
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 1440
        self.user_repository = user_repository

    def encode_token(self, user_id: str, role: str) -> str:
        expiration_time = datetime.now() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "role": role,
            "exp": expiration_time
        }
        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def decode_token(self, token: str) -> Dict:
        try:
            return jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise ExpiredTokenException("Token has expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenException("Invalid authentication token")

    def verify_token(self, token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            payload = self.decode_token(token)
            user_id = payload["sub"]
            role = payload.get("role", "")

            user = self.user_repository.find_by_id(user_id)
            if not user:
                return False, None, None

            return True, user_id, role
        except (InvalidTokenException, ExpiredTokenException) as e:
            raise TokenVerificationException(str(e))

    def token_required(self, f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            token = self._extract_token()

            if not token:
                return jsonify({'error': 'Authentication token is missing'}), 401

            try:
                is_valid, user_id, _ = self.verify_token(token)
                if not is_valid or not user_id:
                    return jsonify({'error': 'Invalid authentication token'}), 401
                return f(user_id, *args, **kwargs)

            except ExpiredTokenException:
                return jsonify({'error': 'Token has expired'}), 401
            except (InvalidTokenException, TokenVerificationException):
                return jsonify({'error': 'Invalid token'}), 401
            except Exception as e:
                return jsonify({'error': str(e)}), 401

        return decorated

    def role_required(self, required_role: str) -> Callable:
        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def decorated(*args, **kwargs):
                token = self._extract_token()

                if not token:
                    return jsonify({'error': 'Authentication token is missing'}), 401

                try:
                    is_valid, user_id, role = self.verify_token(token)
                    if not is_valid or not user_id:
                        return jsonify({'error': 'Invalid authentication token'}), 401


                    if role != required_role:
                        return jsonify({'error': 'Unauthorized access'}), 403

                    return f(user_id, *args, **kwargs)
                except ExpiredTokenException:
                    return jsonify({'error': 'Token has expired'}), 401
                except (InvalidTokenException, TokenVerificationException):
                    return jsonify({'error': 'Invalid token'}), 401
                except Exception as e:
                    return jsonify({'error': str(e)}), 401

            return decorated

        return decorator

    def _extract_token(self) -> Optional[str]:
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token and 'token' in request.args:
            token = request.args.get('token')

        return token