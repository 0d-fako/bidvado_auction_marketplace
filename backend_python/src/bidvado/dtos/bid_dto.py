from dataclasses import dataclass
from datetime import datetime
from typing import *

from .auction_dto import CreateAuctionResponse
from .user_dto import  UserLoginResponse
from ..data.models.enum.enums import *

@dataclass
class PlaceBidRequest:
    auction_id: str
    bidder_id: str
    amount: float


@dataclass
class PlaceBidResponse:
    id: str
    auction: 'CreateAuctionResponse'
    bidder : 'UserLoginResponse'
    amount: float
    created_at: datetime
    is_winning: bool
