from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..data.models.enum.enums import UserRole


@dataclass
class UserRegisterRequest:
    username: str
    email: str
    password: str
    role: UserRole
    profile_picture:Optional[str]=None

@dataclass
class UserRegisterResponse:
    id: str
    username: str
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime
    profile_picture: Optional[str] = None

@dataclass
class UserLoginRequest:
    username: str
    password: str


@dataclass
class UserLoginResponse:
    id: str
    username: str
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime
    access_token: str
    profile_picture: Optional[str] = None
    token_type: str = "Bearer"
