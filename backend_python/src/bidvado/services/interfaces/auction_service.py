from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime

from ...dtos.auction_dto import CreateAuctionRequest, CreateAuctionResponse
from ...data.models.enum.enums import AuctionStatus


class IAuctionService(ABC):
    @abstractmethod
    def create_auction(self, request: CreateAuctionRequest) -> CreateAuctionResponse:
        pass

    @abstractmethod
    def get_auction(self, auction_id: str) -> Optional[CreateAuctionResponse]:
        pass

    @abstractmethod
    def get_auctions(self, page: int = 1, page_size: int = 10,
                    status: Optional[AuctionStatus] = None) -> List[CreateAuctionResponse]:
        pass

    @abstractmethod
    def update_auction(self, auction_id: str, user_id: str, user_role: str,
                       update_data: Dict) -> Optional[CreateAuctionResponse]:
        pass

    @abstractmethod
    def approve_auction(self, auction_id: str, admin_id: str) -> Optional[CreateAuctionResponse]:
        pass

    @abstractmethod
    def cancel_auction(self, auction_id: str, user_id: str, user_role: str) -> bool:
        pass

    @abstractmethod
    def check_expired_auctions(self) -> List[str]:
        pass