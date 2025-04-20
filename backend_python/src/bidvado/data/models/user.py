import datetime
from .enum.enums import UserRole

class User:
    def __init__(self, id=None, username=None, email=None, password=None, role=UserRole, created_at=None, updated_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.role = UserRole
        self.profile_picture = None
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        self.verified = False
        self.reset_token = None
        self.reset_token_expiry = None