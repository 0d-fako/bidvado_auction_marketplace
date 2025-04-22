import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from bson import ObjectId

from src.bidvado.data.models.bid import Bid
from src.bidvado.data.models.auction import Auction
from src.bidvado.data.models.user import User
from src.bidvado.data.repositories.bid_repository import BidRepository
from src.bidvado.exceptions.bid_exceptions import (
    BidException,
    InvalidBidException,
    AuctionClosedException
)

from mongoengine import connect

connect(db="test_bidvado_db", host="mongodb://localhost:27017/", alias="default")


class TestBidRepository(unittest.TestCase):
    def setUp(self):
        self.repo = BidRepository()
        self.mock_bid_id = str(ObjectId())
        self.mock_auction_id = str(ObjectId())
        self.mock_user_id = str(ObjectId())
        self.sample_time = datetime.now()

        # Create mock auction
        self.mock_auction = MagicMock(spec=Auction)
        self.mock_auction.id = self.mock_auction_id
        self.mock_auction.current_bid = 100.0
        self.mock_auction.status.value = "active"

        # Create mock bidder
        self.mock_bidder = MagicMock(spec=User)
        self.mock_bidder.id = self.mock_user_id

        # Create mock bid
        self.test_bid = MagicMock(spec=Bid)
        self.test_bid.id = self.mock_bid_id
        self.test_bid.auction = self.mock_auction
        self.test_bid.bidder = self.mock_bidder
        self.test_bid.amount = 150.0
        self.test_bid.created_at = self.sample_time

    @patch.object(Bid, 'save')
    @patch("mongoengine.queryset.QuerySet.first")
    def test_create_bid_success(self, mock_first, mock_save):
        mock_first.side_effect = [self.mock_auction, self.mock_bidder]
        mock_save.return_value = self.test_bid

        result = self.repo.create(
            auction_id=self.mock_auction_id,
            bidder_id=self.mock_user_id,
            amount=150.0
        )

        self.assertEqual(result, self.mock_bid_id)
        mock_save.assert_called_once()
        self.assertEqual(mock_first.call_count, 2)

    @patch("mongoengine.queryset.QuerySet.first")
    def test_create_bid_invalid_auction(self, mock_first):
        # First call (auction lookup) returns None
        mock_first.return_value = None

        with self.assertRaises(BidException) as context:
            self.repo.create(
                auction_id='invalid_id',
                bidder_id=self.mock_user_id,
                amount=150.0
            )
        self.assertEqual(str(context.exception), "Invalid auction or bidder ID")

    @patch("mongoengine.queryset.QuerySet.first")
    def test_create_bid_invalid_bidder(self, mock_first):
        # First call returns auction, second returns None
        mock_first.side_effect = [self.mock_auction, None]

        with self.assertRaises(BidException) as context:
            self.repo.create(
                auction_id=self.mock_auction_id,
                bidder_id='invalid_id',
                amount=150.0
            )
        self.assertEqual(str(context.exception), "Invalid auction or bidder ID")

    @patch("mongoengine.queryset.QuerySet.first")
    def test_create_bid_amount_too_low(self, mock_first):
        mock_first.side_effect = [self.mock_auction, self.mock_bidder]

        with self.assertRaises(InvalidBidException) as context:
            self.repo.create(
                auction_id=self.mock_auction_id,
                bidder_id=self.mock_user_id,
                amount=50.0  # Below current bid
            )
        self.assertEqual(str(context.exception), "Amount must be greater than current bid")

    @patch("mongoengine.queryset.QuerySet.first")
    def test_create_bid_auction_closed(self, mock_first):
        closed_auction = MagicMock(spec=Auction)
        closed_auction.id = self.mock_auction_id
        closed_auction.current_bid = 100.0
        closed_auction.status.value = "completed"

        mock_first.side_effect = [closed_auction, self.mock_bidder]

        with self.assertRaises(AuctionClosedException) as context:
            self.repo.create(
                auction_id=self.mock_auction_id,
                bidder_id=self.mock_user_id,
                amount=150.0
            )
        self.assertEqual(str(context.exception), "Auction is closed")

    @patch("mongoengine.queryset.QuerySet.first")
    def test_find_by_id_found(self, mock_first):
        mock_first.return_value = self.test_bid
        result = self.repo.find_by_id(self.mock_bid_id)
        self.assertEqual(str(result.id), self.mock_bid_id)

    @patch("mongoengine.queryset.QuerySet.first")
    def test_find_by_id_not_found(self, mock_first):
        mock_first.return_value = None
        result = self.repo.find_by_id(self.mock_bid_id)
        self.assertIsNone(result)

    @patch("mongoengine.queryset.QuerySet.order_by")
    @patch("mongoengine.queryset.QuerySet.skip")
    @patch("mongoengine.queryset.QuerySet.limit")
    @patch("mongoengine.queryset.QuerySet.filter")
    def test_find_many_with_pagination(self, mock_filter, mock_limit, mock_skip, mock_order):
        mock_filter.return_value.order_by.return_value.skip.return_value.limit.return_value = [self.test_bid]

        result = self.repo.find_many(
            filter_criteria={'auction': self.mock_auction_id},
            sort_by='-amount',
            skip=5,
            limit=10
        )

        self.assertEqual(len(result), 1)
        mock_filter.assert_called_with(auction=self.mock_auction_id)
        mock_order.assert_called_with('-amount')
        mock_skip.assert_called_with(5)
        mock_limit.assert_called_with(10)

    @patch("mongoengine.queryset.QuerySet.first")
    @patch("mongoengine.queryset.QuerySet.order_by")
    @patch("mongoengine.queryset.QuerySet.filter")
    def test_find_highest_bid_success(self, mock_filter, mock_order, mock_first):
        mock_filter.return_value.order_by.return_value.first.return_value = self.test_bid

        result = self.repo.find_highest_bid(self.mock_auction_id)

        self.assertEqual(result.amount, 150.0)
        mock_filter.assert_called_with(auction=self.mock_auction)
        mock_order.assert_called_with('-amount')

    @patch("mongoengine.queryset.QuerySet.first")
    def test_find_highest_bid_invalid_auction(self, mock_first):
        mock_first.return_value = None

        with self.assertRaises(BidException) as context:
            self.repo.find_highest_bid('invalid_auction_id')
        self.assertEqual(str(context.exception), "Invalid auction ID")

    @patch("mongoengine.queryset.QuerySet.modify")
    @patch("mongoengine.queryset.QuerySet.first")
    def test_update_bid_success(self, mock_first, mock_modify):
        mock_first.return_value = self.test_bid
        mock_modify.return_value = self.test_bid

        result = self.repo.update(
            bid_id=self.mock_bid_id,
            update_data={'amount': 175.0}
        )

        self.assertEqual(result.id, self.mock_bid_id)
        mock_modify.assert_called_once()

    @patch("mongoengine.queryset.QuerySet.modify")
    @patch("mongoengine.queryset.QuerySet.first")
    def test_update_bid_not_found(self, mock_first, mock_modify):
        mock_first.return_value = None

        with self.assertRaises(BidException) as context:
            self.repo.update(
                bid_id='invalid_bid_id',
                update_data={'amount': 175.0}
            )
        self.assertEqual(str(context.exception), "Invalid bid ID")

    @patch("mongoengine.queryset.QuerySet.count")
    def test_count_bids(self, mock_count):
        mock_count.return_value = 5
        result = self.repo.count({'auction': self.mock_auction_id})
        self.assertEqual(result, 5)
        mock_count.assert_called_with(auction=self.mock_auction_id)


if __name__ == '__main__':
    unittest.main()