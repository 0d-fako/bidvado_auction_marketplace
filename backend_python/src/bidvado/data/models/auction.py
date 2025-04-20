from mongoengine import *
import datetime
from .user import User
from .enum.enums import AuctionStatus

class Auction(Document):
    title = StringField(required=True)
    description = StringField()
    images = ListField(StringField())
    seller = ReferenceField(User, required=True)
    starting_bid = DecimalField(required=True, precision=2)
    current_bid = DecimalField(default=0.00, precision=2)
    bid_increment = DecimalField(required=True, precision=2)
    start_time = DateTimeField(required=True)
    end_time = DateTimeField(required=True)
    status = EnumField(AuctionStatus, default=AuctionStatus.PENDING)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    approved_by = ReferenceField(User, null=True)
    approved_at = DateTimeField(null=True)

    meta = {'collection': 'auctions'}