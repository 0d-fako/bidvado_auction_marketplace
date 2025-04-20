from dataclasses import dataclass
from datetime import datetime
from typing import *

from .user_dto import UserRegisterResponse
from ..data.models.enum.enums import *

@dataclass
class CreateAuctionRequest:
    title: str
    seller_id: str
    starting_bid: float
    bid_increment: float
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    images: Optional[List[str]] = None



@dataclass
class CreateAuctionResponse:
    id: str
    title: str
    description: Optional[str]
    images: List[str]
    seller: 'UserRegisterResponse'
    starting_bid: float
    current_bid: Optional[float]
    bid_increment: float
    start_time: datetime
    end_time: datetime
    status: AuctionStatus
    created_at: datetime
    updated_at: datetime
    approved_by: Optional['UserRegisterResponse'] = None
    approved_at: Optional[datetime] = None


