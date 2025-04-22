from abc import ABC, abstractmethod
from typing import List, Optional, Dict

from ...dtos.bid_dto import PlaceBidRequest, PlaceBidResponse


class IBidService(ABC):
    @abstractmethod
    def place_bid(self, request: PlaceBidRequest) -> PlaceBidResponse:
        pass

    @abstractmethod
    def get_bid(self, bid_id: str) -> Optional[PlaceBidResponse]:
        pass

    @abstractmethod
    def get_auction_bids(self, auction_id: str, page: int = 1,
                        page_size: int = 10) -> List[PlaceBidResponse]:
        pass

    @abstractmethod
    def get_highest_bid(self, auction_id: str) -> Optional[PlaceBidResponse]:
        pass