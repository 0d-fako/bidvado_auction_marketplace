import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple

from ..exceptions.auth_exceptions import InvalidTokenException, ExpiredTokenException, TokenVerificationException

# Use an environment variable for the secret key
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your_default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def encode_token(user_id: str, role: str) -> str:
    expiration_time = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expiration_time
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ExpiredTokenException("Token has expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenException("Invalid authentication token")

def verify_token(token: str) -> Tuple[bool, Optional[str]]:
    try:
        payload = decode_token(token)
        return True, payload["sub"]
    except (InvalidTokenException, ExpiredTokenException) as e:
        raise TokenVerificationException(str(e))
    # return False, None
