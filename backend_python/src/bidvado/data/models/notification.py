from mongoengine import *
from datetime import datetime
from .user import User
from auction import Auction
from .enum.enums import NotificationType

class Notification(Document):
    user = ReferenceField(User, required=True)
    auction = ReferenceField(Auction, null=True)
    type = StringField(NotificationType, required=True)
    message = StringField(required=True)
    is_read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now)

    meta = {'collection': 'notifications'}