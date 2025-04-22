import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from .interfaces.auth_service import IAuthService
from ..data.repositories.user_repository import UserRepository
from ..dtos.user_dto import UserRegisterRequest, UserRegisterResponse, UserLoginRequest, UserLoginResponse
from ..exceptions.auth_exceptions import InvalidCredentialsException, InvalidTokenException, ExpiredTokenException


class AuthService(IAuthService):
    def __init__(self, user_repository: UserRepository, secret_key: str, token_expiry: int = 24):
        self.user_repository = user_repository
        self.secret_key = secret_key
        self.token_expiry = token_expiry

    def register(self, request: UserRegisterRequest) -> UserRegisterResponse:
        password_hash = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


        user_id = self.user_repository.create(
            username=request.username,
            email=request.email,
            password_hash=password_hash,
            role=request.role.value
        )


        user = self.user_repository.find_by_id(user_id)


        return UserRegisterResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
            profile_picture=user.profile_picture
        )

    def login(self, request: UserLoginRequest) -> UserLoginResponse:
        user = self.user_repository.find_by_email(request.username)
        if not user:
            raise InvalidCredentialsException()

        if not bcrypt.checkpw(request.password.encode('utf-8'), user.password.encode('utf-8')):
            raise InvalidCredentialsException()


        expiry = datetime.now() + timedelta(hours=self.token_expiry)
        token_payload = {
            'sub': str(user.id),
            'role': user.role,
            'exp': expiry
        }
        access_token = jwt.encode(token_payload, self.secret_key, algorithm='HS256')


        return UserLoginResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
            access_token=access_token,
            profile_picture=user.profile_picture
        )

    def validate_token(self, token: str) -> Tuple[bool, Optional[str]]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_id = payload['sub']

            user = self.user_repository.find_by_id(user_id)
            if not user:
                return False, None
            return True, user_id
        except jwt.ExpiredSignatureError:
            raise ExpiredTokenException()
        except jwt.InvalidTokenError:
            raise InvalidTokenException()

    def request_password_reset(self, email: str) -> bool:
        user = self.user_repository.find_by_email(email)
        if not user:

            return False


        reset_token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=24)


        self.user_repository.update(
            user_id=str(user.id),
            reset_token=reset_token,
            reset_token_expiry=expiry
        )

        return True

    def reset_password(self, token: str, new_password: str) -> bool:
        user = self.user_repository.find_by_reset_token(token)
        if not user:
            return False

        if user.reset_token_expiry < datetime.now():
            return False

        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


        self.user_repository.update(
            user_id=str(user.id),
            password=password_hash,
            reset_token=None,
            reset_token_expiry=None
        )
        return True