from datetime import datetime, timedelta
from typing import Optional, Tuple
import bcrypt

from src.bidvado.utils.jwt_handler import JWTManager
from src.bidvado.dtos.user_dto import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserLoginResponse
)
from src.bidvado.exceptions.auth_exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    TokenVerificationException,
    UserCreationException
)
from src.bidvado.services.interfaces.auth_service import IAuthService
from src.bidvado.data.repositories.user_repository import UserRepository


class AuthService(IAuthService):
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository
        self.jwt_manager = JWTManager()

    def register(self, request: UserRegisterRequest) -> UserRegisterResponse:
        if self.user_repo.find_by_email(request.email):
            raise UserAlreadyExistsException("Email already registered")

        user_id = self.user_repo.create(
            username=request.username,
            email=request.email,
            password_hash=self._hash_password(request.password),
            role=request.role.value
        )

        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise UserCreationException("Failed to create user")

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
        user = self.user_repo.find_by_email(request.email)
        if not user or not self._verify_password(request.password, user.password):
            raise InvalidCredentialsException("Invalid credentials")

        token = self.jwt_manager.encode_token(
            user_id=str(user.id),
            role=user.role
        )

        return UserLoginResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
            access_token=token,
            role=user.role,
            profile_picture=user.profile_picture,
            token_type = "bearer",

        )

    def validate_token(self, token: str) -> Tuple[bool, Optional[str]]:
        try:
            valid, user_id = self.jwt_manager.verify_token(token)
            return valid and bool(self.user_repo.find_by_id(user_id)), user_id
        except TokenVerificationException:
            return False, None

    def request_password_reset(self, email: str) -> bool:
        user = self.user_repo.find_by_email(email)
        if not user:
            return True

        reset_token = self.jwt_manager.encode_token(
            user_id=str(user.id),
            role=user.role.value
        )

        self.user_repo.update(
            user_id=str(user.id),
            reset_token=reset_token,
            reset_token_expiry=datetime.now() + timedelta(minutes=30)
        )
        return True

    def reset_password(self, token: str, new_password: str) -> bool:
        try:
            valid, user_id = self.jwt_manager.verify_token(token)
            if not valid or not user_id:
                return False

            user = self.user_repo.find_by_reset_token(token)
            if not user or datetime.now() > user.reset_token_expiry:
                return False

            return self.user_repo.update(
                user_id=user_id,
                password=self._hash_password(new_password),
                reset_token=None,
                reset_token_expiry=None
            )
        except TokenVerificationException:
            return False

    @staticmethod
    def _hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def _verify_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))