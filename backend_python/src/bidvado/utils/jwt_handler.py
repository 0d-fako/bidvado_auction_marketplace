import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple

from ..exceptions.auth_exceptions import (
    InvalidTokenException,
    ExpiredTokenException,
    TokenVerificationException
)

class JWTManager:
    def __init__(self):
        self.SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your_default_secret_key_should_be_strong")
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 60

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

    def verify_token(self, token: str) -> Tuple[bool, Optional[str]]:
        try:
            payload = self.decode_token(token)
            return True, payload["sub"]
        except (InvalidTokenException, ExpiredTokenException) as e:
            raise TokenVerificationException(str(e))