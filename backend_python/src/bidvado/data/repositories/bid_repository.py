from datetime import datetime
from typing import Optional, List, Dict
from ..models.bid import Bid
from ..models.auction import Auction
from ..models.user import User
from ..models.enum.enums import AuctionStatus
from ...exceptions.bid_exceptions import BidException, InvalidBidException, AuctionClosedException


class BidRepository:

    def create(self, auction_id: str, bidder_id: str, amount: float) -> str:
        auction = Auction.objects(id=auction_id).first()
        bidder = User.objects(id=bidder_id).first()

        if not auction or not bidder:
            raise BidException("Invalid auction or bidder ID")


        if auction.status != AuctionStatus.ACTIVE.value:
            raise AuctionClosedException("Cannot place bid on a non-active auction")


        if auction.current_bid is None:
            minimum_bid = auction.starting_bid
        else:
            minimum_bid = auction.current_bid + auction.bid_increment

        if float(amount) < float(minimum_bid):
            raise InvalidBidException(f"Bid amount must be at least {minimum_bid}")


        current_winning_bid = Bid.objects(auction=auction, is_winning=True).first()
        if current_winning_bid:
            current_winning_bid.is_winning = False
            current_winning_bid.save()


        bid = Bid(
            auction=auction,
            bidder=bidder,
            amount=amount,
            created_at=datetime.now(),
            is_winning=True
        ).save()


        auction.current_bid = amount
        auction.updated_at = datetime.now()
        auction.save()

        return str(bid.id)

    def find_by_id(self, bid_id: str) -> Optional[Bid]:
        return Bid.objects(id=bid_id).first()

    def find_many(self, filter_criteria: Dict = None, sort_by: str = "-created_at",
                  page: int = 1, page_size: int = 10) -> List[Bid]:

        skip = (page - 1) * page_size
        query = Bid.objects(**(filter_criteria or {})).order_by(sort_by)
        return list(query.skip(skip).limit(page_size))

    def find_by_auction(self, auction_id: str, page: int = 1, page_size: int = 10) -> List[Bid]:

        auction = Auction.objects(id=auction_id).first()
        if not auction:
            raise BidException("Invalid auction ID")

        return self.find_many({'auction': auction}, sort_by="-created_at",
                              page=page, page_size=page_size)

    def find_highest_bid(self, auction_id: str) -> Optional[Bid]:
        auction = Auction.objects(id=auction_id).first()
        if not auction:
            raise BidException("Invalid auction ID")

        return Bid.objects(auction=auction, is_winning=True).first() or \
            Bid.objects(auction=auction).order_by("-amount").first()

    def count(self, filter_criteria: Dict = None) -> int:
        return Bid.objects(**(filter_criteria or {})).count()