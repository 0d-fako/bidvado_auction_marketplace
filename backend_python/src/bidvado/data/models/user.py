from mongoengine import *
import datetime
from .enum.enums import UserRole

class User(Document):
    username = StringField(required=True, unique=True)
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    role = EnumField(UserRole, required=True)
    profile_picture = StringField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    reset_token = StringField(null=True)
    reset_token_expiry = DateTimeField(null=True)

    meta = {'collection': 'users'}