from abc import ABC, abstractmethod
from typing import Optional, Tuple

from ...dtos.user_dto import UserRegisterRequest, UserRegisterResponse, UserLoginRequest, UserLoginResponse


class IAuthService(ABC):
    @abstractmethod
    def register(self, request: UserRegisterRequest) -> UserRegisterResponse:
        pass

    @abstractmethod
    def login(self, request: UserLoginRequest) -> UserLoginResponse:
        pass

    @abstractmethod
    def validate_token(self, token: str) -> Tuple[bool, Optional[str]]:
        pass

    @abstractmethod
    def request_password_reset(self, email: str) -> bool:
        pass

    @abstractmethod
    def reset_password(self, token: str, new_password: str) -> bool:
        pass