from mongoengine import *
from datetime import datetime
from auction import Auction
from user import User

class Bid(Document):
    auction = ReferenceField(Auction, required=True)
    bidder = ReferenceField(User, required=True)
    amount = DecimalField(required=True, precision=2, min_value=0.00)
    created_at = DateTimeField(default=datetime.now)
    is_winning = BooleanField(default=False)

    meta = {"collection": "bid"}