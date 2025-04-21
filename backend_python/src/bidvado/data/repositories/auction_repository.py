from datetime import datetime
from typing import Optional, List, Dict
from ..models.auction import Auction
from ..models.enum.enums import AuctionStatus, UserRole
from ..models.user import User
from ...exceptions.auction_exceptions import AuctionNotFoundException, InvalidAuctionStateException
from ...exceptions.auth_exceptions import NoSuchUserException, InvalidActionException


class AuctionRepository:
    def create(self, title: str, auctioneer_id: str, starting_bid: float,
               bid_increment: float, end_time: datetime,
               description: Optional[str] = None,
               images: Optional[List[str]] = None) -> str:

        auctioneer = User.objects(id=auctioneer_id).first()
        if not auctioneer:
            raise NoSuchUserException("User does not exist")
        if auctioneer.role != UserRole.AUCTIONEER:
            raise InvalidActionException("Only auctioneers can create auctions")

        if end_time <= datetime.now():
            raise InvalidAuctionStateException("End time must be in the future")

        auction = Auction(
            title=title,
            description=description,
            images=images or [],
            auctioneer=auctioneer,
            starting_bid=starting_bid,
            bid_increment=bid_increment,
            start_time=datetime.now(),
            end_time=end_time,
            status=AuctionStatus.PENDING.value,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ).save()

        return str(auction.id)

    def find_by_id(self, auction_id: str) -> Optional[Auction]:
        return Auction.objects(id=auction_id).first()

    def find_all(self, page: int = 1, page_size: int = 10) -> List[Auction]:
        skip_count = (page - 1) * page_size
        return list(Auction.objects.order_by('-created_at').skip(skip_count).limit(page_size))

    def find_by_status(self, status: AuctionStatus) -> List[Auction]:
        return list(Auction.objects(status=status.value).order_by('-created_at'))

    def update(self, auction_id: str, user_role: str, **update_data) -> Optional[Auction]:
        auction = self.find_by_id(auction_id)
        if not auction:
            raise AuctionNotFoundException("Auction not found")

        if 'status' in update_data:
            if not self._is_valid_status_change(auction.status, update_data['status']):
                raise InvalidAuctionStateException("Invalid status transition")
            if (auction.status != AuctionStatus.PENDING.value and
                    user_role != UserRole.ADMIN.value):
                raise InvalidActionException("Only admins can modify non-pending auctions")

        update_data['updated_at'] = datetime.now()
        result = Auction.objects(id=auction_id).update_one(**update_data)

        if result == 0:
            return None
        return self.find_by_id(auction_id)

    def delete(self, auction_id: str, user_role: str) -> bool:
        auction = self.find_by_id(auction_id)
        if not auction:
            raise AuctionNotFoundException()

        if auction.status != AuctionStatus.PENDING.value and user_role != UserRole.ADMIN.value:
            raise InvalidActionException("Only admins can delete non-pending auctions")

        auction.delete()
        return True

    def count(self, filter_criteria: Dict = None) -> int:
        return Auction.objects(**filter_criteria).count() if filter_criteria else Auction.objects.count()

    def _is_valid_status_change(self, current_status: str, new_status: str) -> bool:
        valid_transitions = {
            AuctionStatus.PENDING.value: [
                AuctionStatus.APPROVED.value,
                AuctionStatus.CANCELLED.value
            ],
            AuctionStatus.APPROVED.value: [
                AuctionStatus.ACTIVE.value,
                AuctionStatus.CANCELLED.value
            ],
            AuctionStatus.ACTIVE.value: [
                AuctionStatus.COMPLETED.value,
                AuctionStatus.CANCELLED.value
            ]
        }
        return new_status in valid_transitions.get(current_status, [])