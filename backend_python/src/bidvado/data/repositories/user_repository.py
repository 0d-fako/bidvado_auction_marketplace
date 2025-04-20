from datetime import datetime
from typing import Optional
from ..models.user import User
from ...exceptions.auth_exceptions import UserAlreadyExistsException, NoSuchUserException


class UserRepository:
    def create(self, username: str, email: str, password_hash: str, role: str) -> str:
        if User.objects(email=email).first():
            raise UserAlreadyExistsException()

        user = User(
            username=username,
            email=email,
            password=password_hash,
            role=role,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ).save()
        return str(user.id)

    def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID"""
        return User.objects(id=user_id).first()

    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        return User.objects(email=email).first()

    def find_by_reset_token(self, token: str) -> Optional[User]:
        """Find user by reset token"""
        return User.objects(reset_token=token).first()

    def update(self, user_id: str, **update_data) -> bool:
        """Update user"""
        user = self.find_by_id(user_id)
        if not user:
            raise NoSuchUserException()

        update_data['updated_at'] = datetime.now()
        user.update(**update_data)
        return True

    def delete(self, user_id: str) -> bool:
        """Delete user"""
        user = self.find_by_id(user_id)
        if not user:
            return False
        user.delete()
        return True