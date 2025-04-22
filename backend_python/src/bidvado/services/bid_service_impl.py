from typing import List, Optional

from .interfaces.bid_service import IBidService
from ..data.repositories.bid_repository import BidRepository
from ..data.repositories.auction_repository import AuctionRepository
from ..data.repositories.user_repository import UserRepository
from ..dtos.bid_dto import PlaceBidRequest, PlaceBidResponse
# from ..dtos.auction_dto import CreateAuctionResponse
from ..dtos.user_dto import UserLoginResponse
# from ..exceptions.bid_exceptions import BidException
from ..exceptions.auction_exceptions import AuctionNotFoundException
from ..exceptions.auth_exceptions import NoSuchUserException
from ..websockets.event_emitter import EventEmitter


class BidService(IBidService):
    def __init__(self,
                 bid_repository: BidRepository,
                 auction_repository: AuctionRepository,
                 user_repository: UserRepository,
                 notification_service,
                 event_emitter: EventEmitter):
        self.bid_repository = bid_repository
        self.auction_repository = auction_repository
        self.user_repository = user_repository
        self.notification_service = notification_service
        self.event_emitter = event_emitter

    def place_bid(self, request: PlaceBidRequest) -> PlaceBidResponse:
        auction = self.auction_repository.find_by_id(request.auction_id)
        if not auction:
            raise AuctionNotFoundException()

        bidder = self.user_repository.find_by_id(request.bidder_id)
        if not bidder:
            raise NoSuchUserException()


        previous_bid = self.bid_repository.find_highest_bid(request.auction_id)
        previous_bidder_id = str(previous_bid.bidder.id) if previous_bid else None


        bid_id = self.bid_repository.create(
            auction_id=request.auction_id,
            bidder_id=request.bidder_id,
            amount=request.amount
        )


        bid = self.bid_repository.find_by_id(bid_id)


        if previous_bidder_id and previous_bidder_id != request.bidder_id:
            self.notification_service.notify_outbid(
                auction_id=request.auction_id,
                previous_bidder_id=previous_bidder_id,
                new_bid_amount=request.amount
            )


        self._emit_bid_event(bid)


        return self._map_to_dto(bid)

    def get_bid(self, bid_id: str) -> Optional[PlaceBidResponse]:
        bid = self.bid_repository.find_by_id(bid_id)
        if not bid:
            return None

        return self._map_to_dto(bid)

    def get_auction_bids(self, auction_id: str, page: int = 1,
                         page_size: int = 10) -> List[PlaceBidResponse]:
        bids = self.bid_repository.find_by_auction(auction_id, page, page_size)
        return [self._map_to_dto(bid) for bid in bids]

    def get_highest_bid(self, auction_id: str) -> Optional[PlaceBidResponse]:
        bid = self.bid_repository.find_highest_bid(auction_id)
        if not bid:
            return None

        return self._map_to_dto(bid)

    def _emit_bid_event(self, bid):
        event_data = {
            'auction_id': str(bid.auction.id),
            'bid_id': str(bid.id),
            'bidder_id': str(bid.bidder.id),
            'bidder_username': bid.bidder.username,
            'amount': float(bid.amount),
            'created_at': bid.created_at.isoformat(),
            'is_winning': bid.is_winning
        }


        self.event_emitter.emit('new_bid', event_data, f'auction_{bid.auction.id}')


        self.event_emitter.emit('auction_update', event_data)

    def _map_to_dto(self, bid) -> PlaceBidResponse:
        from ..services.auction_service_impl import AuctionService


        auction_service = AuctionService(self.auction_repository, self.user_repository)
        auction_dto = auction_service._map_to_dto(bid.auction)


        bidder_dto = UserLoginResponse(
            id=str(bid.bidder.id),
            username=bid.bidder.username,
            email=bid.bidder.email,
            role=bid.bidder.role,
            created_at=bid.bidder.created_at,
            updated_at=bid.bidder.updated_at,
            access_token="",
            profile_picture=bid.bidder.profile_picture
        )

        return PlaceBidResponse(
            id=str(bid.id),
            auction=auction_dto,
            bidder=bidder_dto,
            amount=float(bid.amount),
            created_at=bid.created_at,
            is_winning=bid.is_winning
        )