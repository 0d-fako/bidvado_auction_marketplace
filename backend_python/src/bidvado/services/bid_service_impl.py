from typing import List, Optional

from .interfaces.bid_service import IBidService
from ..data.repositories.bid_repository import BidRepository
from ..data.repositories.auction_repository import AuctionRepository
from ..data.repositories.user_repository import UserRepository
from ..dtos.bid_dto import PlaceBidRequest, PlaceBidResponse
from ..dtos.auction_dto import CreateAuctionResponse
from ..dtos.user_dto import UserLoginResponse, UserRegisterResponse
from ..exceptions.auction_exceptions import AuctionNotFoundException
from ..exceptions.auth_exceptions import NoSuchUserException
from ..websockets.websocket_handler import WebSocketHandler


class BidService(IBidService):
    def __init__(self,
                 bid_repository: BidRepository,
                 auction_repository: AuctionRepository,
                 user_repository: UserRepository,
                 notification_service,
                 websocket_handler: WebSocketHandler):
        self.bid_repository = bid_repository
        self.auction_repository = auction_repository
        self.user_repository = user_repository
        self.notification_service = notification_service
        self.websocket_handler = websocket_handler

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


        if previous_bidder_id and previous_bidder_id != request.bidder_id and self.notification_service:
            self.notification_service.notify_outbid(
                auction_id=request.auction_id,
                previous_bidder_id=previous_bidder_id,
                new_bid_amount=request.amount
            )


        self._send_bid_update(bid)


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

    def _send_bid_update(self, bid):

        bid_data = {
            'auction_id': str(bid.auction.id),
            'bid_id': str(bid.id),
            'bidder_id': str(bid.bidder.id),
            'bidder_username': bid.bidder.username,
            'amount': float(bid.amount),
            'created_at': bid.created_at.isoformat(),
            'is_winning': bid.is_winning
        }

        self.websocket_handler.emit_to_auction(
            auction_id=str(bid.auction.id),
            event='new_bid',
            data=bid_data
        )

    def get_user_bids(self, user_id: str, page: int = 1,
                          page_size: int = 10) -> List[PlaceBidResponse]:

            user = self.user_repository.find_by_id(user_id)
            if not user:
                raise NoSuchUserException("User not found")

            bids = self.bid_repository.find_by_bidder(user_id, page, page_size)
            return [self._map_to_dto(bid) for bid in bids]

    def _map_to_dto(self, bid) -> PlaceBidResponse:
        auction_dto = CreateAuctionResponse(
            id=str(bid.auction.id),
            title=bid.auction.title,
            description=bid.auction.description,
            images=bid.auction.images,
            auctioneer_id=self._map_user_to_dto(bid.auction.auctioneer),
            starting_bid=float(bid.auction.starting_bid),
            current_bid=float(bid.auction.current_bid) if bid.auction.current_bid else None,
            bid_increment=float(bid.auction.bid_increment),
            start_time=bid.auction.start_time,
            end_time=bid.auction.end_time,
            status=bid.auction.status,
            created_at=bid.auction.created_at,
            updated_at=bid.auction.updated_at,
            approved_by=self._map_user_to_dto(bid.auction.approved_by) if bid.auction.approved_by else None,
            approved_at=bid.auction.approved_at
        )

        bidder_dto = UserLoginResponse(
            id=str(bid.bidder.id),
            username=bid.bidder.username,
            email=bid.bidder.email,
            role=bid.bidder.role,
            created_at=bid.bidder.created_at,
            updated_at=bid.bidder.updated_at,
            access_token="",  # Empty token as it's not needed here
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

    def _map_user_to_dto(self, user) -> Optional[UserRegisterResponse]:
        if not user:
            return None

        return UserRegisterResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
            profile_picture=user.profile_picture
        )