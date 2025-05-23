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
        return User.objects(id=user_id).first()


    def find_by_username(self, username: str) -> Optional[User]:
        return User.objects(username=username).first()

    def find_by_email(self, email: str) -> Optional[User]:
        return User.objects(email=email).first()

    def find_by_reset_token(self, token: str) -> Optional[User]:
        return User.objects(reset_token=token).first()

    def update(self, user_id: str, **update_data) -> bool:
        user = self.find_by_id(user_id)
        if not user:
            raise NoSuchUserException()

        update_data['updated_at'] = datetime.now()
        user.update(**update_data)
        return True

    def delete(self, user_id: str) -> bool:
        user = self.find_by_id(user_id)
        if not user:
            raise NoSuchUserException("User not found.")
        user.delete()
        return True

