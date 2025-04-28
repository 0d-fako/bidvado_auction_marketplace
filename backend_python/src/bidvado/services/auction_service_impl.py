from datetime import datetime
from typing import List, Optional, Dict

from .interfaces.auction_service import IAuctionService
from ..data.repositories.auction_repository import AuctionRepository
from ..data.repositories.user_repository import UserRepository
from ..dtos.auction_dto import CreateAuctionRequest, CreateAuctionResponse
from ..dtos.user_dto import UserRegisterResponse
from ..data.models.enum.enums import AuctionStatus, UserRole
from ..exceptions.auction_exceptions import AuctionNotFoundException, InvalidAuctionStateException
from ..exceptions.auth_exceptions import InvalidActionException


class AuctionService(IAuctionService):

    def __init__(self, auction_repository: AuctionRepository, user_repository: UserRepository):
        self.auction_repository = auction_repository
        self.user_repository = user_repository

    def create_auction(self, request: CreateAuctionRequest) -> CreateAuctionResponse:

        auction_id = self.auction_repository.create(
            title=request.title,
            auctioneer_id=request.seller_id,
            starting_bid=request.starting_bid,
            bid_increment=request.bid_increment,
            end_time=request.end_time,
            description=request.description,
            images=request.images
        )

        auction = self.auction_repository.find_by_id(auction_id)
        if not auction:
            raise AuctionNotFoundException("Failed to create auction")

        return self._map_to_dto(auction)

    def get_auction(self, auction_id: str) -> Optional[CreateAuctionResponse]:

        auction = self.auction_repository.find_by_id(auction_id)
        if not auction:
            return None

        return self._map_to_dto(auction)

    def get_auctions(self, page: int = 1, page_size: int = 10,
                     status: Optional[AuctionStatus] = None) -> List[CreateAuctionResponse]:
        if status:
            auctions = self.auction_repository.find_by_status(status)
        else:
            auctions = self.auction_repository.find_all(page, page_size)

        return [self._map_to_dto(auction) for auction in auctions]

    def update_auction(self, auction_id: str, user_id: str, user_role: str,
                       update_data: Dict) -> Optional[CreateAuctionResponse]:

        auction = self.auction_repository.find_by_id(auction_id)
        if not auction:
            raise AuctionNotFoundException("Auction not found")

        if str(auction.auctioneer.id) != user_id and user_role != UserRole.ADMIN.value:
            raise InvalidActionException("Only the auctioneer or admin can update this auction")


        updated_auction = self.auction_repository.update(auction_id, user_role, **update_data)
        if not updated_auction:
            return None

        return self._map_to_dto(updated_auction)

    def approve_auction(self, auction_id: str, user_id: str) -> Optional[CreateAuctionResponse]:

        admin = self.user_repository.find_by_id(user_id)
        if not admin or admin.role != UserRole.ADMIN.value:
            raise InvalidActionException("Only admins can approve auctions")


        update_data = {
            'status': AuctionStatus.APPROVED.value,
            'approved_by': admin,
            'approved_at': datetime.now()
        }

        updated_auction = self.auction_repository.update(auction_id, UserRole.ADMIN.value, **update_data)
        if not updated_auction:
            return None

        return self._map_to_dto(updated_auction)

    def cancel_auction(self, auction_id: str, user_id: str, user_role: str) -> bool:
        auction = self.auction_repository.find_by_id(auction_id)
        if not auction:
            raise AuctionNotFoundException("Auction not found")

        if str(auction.auctioneer.id) != user_id and user_role != UserRole.ADMIN.value:
            raise InvalidActionException("Only the auctioneer or admin can cancel an auction")


        if auction.status == AuctionStatus.COMPLETED.value:
            raise InvalidAuctionStateException("Cannot cancel a completed auction")

        update_data = {'status': AuctionStatus.CANCELLED.value}
        updated_auction = self.auction_repository.update(auction_id, user_role, **update_data)

        return updated_auction is not None

    def check_expired_auctions(self) -> List[str]:
        now = datetime.now()
        active_auctions = self.auction_repository.find_by_status(AuctionStatus.ACTIVE)

        updated_ids = []
        for auction in active_auctions:
            if auction.end_time <= now:
                update_data = {'status': AuctionStatus.COMPLETED.value}
                self.auction_repository.update(
                    str(auction.id),
                    UserRole.ADMIN.value,  # System update acts as admin
                    **update_data
                )
                updated_ids.append(str(auction.id))

        return updated_ids

    def activate_approved_auctions(self) -> List[str]:
        approved_auctions = self.auction_repository.find_by_status(AuctionStatus.APPROVED)

        activated_ids = []
        for auction in approved_auctions:
            if auction.start_time <= datetime.now():
                update_data = {'status': AuctionStatus.ACTIVE.value}
                self.auction_repository.update(
                    str(auction.id),
                    UserRole.ADMIN.value,
                    **update_data
                )
                activated_ids.append(str(auction.id))
        return activated_ids

    def _map_to_dto(self, auction) -> CreateAuctionResponse:
        seller = self._map_user_to_dto(auction.auctioneer)
        approved_by = self._map_user_to_dto(auction.approved_by) if auction.approved_by else None

        return CreateAuctionResponse(
            id=str(auction.id),
            title=auction.title,
            description=auction.description,
            images=auction.images,
            seller=seller,
            starting_bid=float(auction.starting_bid),
            current_bid=float(auction.current_bid) if auction.current_bid else None,
            bid_increment=float(auction.bid_increment),
            start_time=auction.start_time,
            end_time=auction.end_time,
            status=auction.status,
            created_at=auction.created_at,
            updated_at=auction.updated_at,
            approved_by=approved_by,
            approved_at=auction.approved_at
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