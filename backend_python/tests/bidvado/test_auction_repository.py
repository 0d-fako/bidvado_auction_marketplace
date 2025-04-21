import unittest
from unittest import mock
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
from bson import ObjectId

from src.bidvado.data.models.auction import Auction
from src.bidvado.data.models.user import User
from src.bidvado.data.models.enum.enums import AuctionStatus, UserRole
from src.bidvado.exceptions.auction_exceptions import AuctionNotFoundException, InvalidAuctionStateException
from src.bidvado.exceptions.auth_exceptions import NoSuchUserException, InvalidActionException
from src.bidvado.data.repositories.auction_repository import AuctionRepository

from mongoengine import connect

connect(db="test_bidvado_db", host="mongodb://localhost:27017/", alias="default")

class TestAuctionRepository(unittest.TestCase):
    def setUp(self):
        self.repo = AuctionRepository()
        self.mock_auction_id = str(ObjectId())
        self.mock_user_id = str(ObjectId())
        self.sample_time = datetime.now()
        self.end_time = datetime.now() + timedelta(days=7)


        self.mock_auctioneer = User(
            id=self.mock_user_id,
            username="auctioneer_user",
            email="auctioneer@example.com",
            password="hashed_password",
            role=UserRole.AUCTIONEER.value,
            created_at=self.sample_time,
            updated_at=self.sample_time
        )

        self.test_auction = Auction(
            id=self.mock_auction_id,
            title="Test Auction",
            description="Test Description",
            images=[],
            auctioneer=self.mock_auctioneer,
            starting_bid=100.0,
            bid_increment=10.0,
            start_time=self.sample_time,
            end_time=self.end_time,
            status=AuctionStatus.PENDING.value,
            created_at=self.sample_time,
            updated_at=self.sample_time
        )

    @patch.object(Auction, "save")
    @patch("mongoengine.queryset.QuerySet.first")
    def test_create_auction_success(self, mock_user_first, mock_save):
        mock_user_id = str(ObjectId())
        mock_auction_id = str(ObjectId())

        mock_auctioneer = User(
            id=mock_user_id,
            username="test_auctioneer",
            email="test@example.com",
            password="hashed_password"
        )
        mock_auctioneer.role = UserRole.AUCTIONEER

        mock_user_first.return_value = mock_auctioneer


        mock_auction = Mock(spec=Auction)
        mock_auction.id = mock_auction_id
        mock_save.return_value = mock_auction

        result = self.repo.create(
            title="Test Auction",
            auctioneer_id=str(mock_user_id),
            starting_bid=100.0,
            bid_increment=10.0,
            end_time=self.end_time
        )

        self.assertEqual(result, mock_auction_id)
        mock_save.assert_called_once()

    @patch("mongoengine.queryset.QuerySet.first")
    def test_create_auction_invalid_user(self, mock_user_first):
        mock_user_first.return_value = None

        with self.assertRaises(NoSuchUserException):
            self.repo.create(
                title="Test Auction",
                auctioneer_id="invalid_id",
                starting_bid=100.0,
                bid_increment=10.0,
                end_time=self.end_time
            )

    @patch("mongoengine.queryset.QuerySet.first")
    def test_find_by_id_found(self, mock_first):
        mock_first.return_value = self.test_auction
        result = self.repo.find_by_id(self.mock_auction_id)
        self.assertEqual(str(result.id), self.mock_auction_id)

    @patch("mongoengine.queryset.QuerySet.first")
    def test_find_by_id_not_found(self, mock_first):
        mock_first.return_value = None
        result = self.repo.find_by_id(self.mock_auction_id)
        self.assertIsNone(result)

    @patch("mongoengine.queryset.QuerySet.order_by")
    def test_find_all(self, mock_order):
        mock_order.return_value.skip.return_value.limit.return_value = [self.test_auction]

        result = self.repo.find_all(page=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(str(result[0].id), self.mock_auction_id)

    @patch("mongoengine.queryset.QuerySet.filter")
    @patch("mongoengine.queryset.QuerySet.order_by")
    def test_find_by_status(self, mock_order_by, mock_filter):
        mock_filter.return_value = mock_filter
        mock_order_by.return_value = [self.test_auction]
        mock_filter.order_by = mock_order_by

        result = self.repo.find_by_status(AuctionStatus.PENDING)
        self.assertEqual(len(result), 1)
        print(result[0].status)
        self.assertEqual(result[0].status, AuctionStatus.PENDING)


    @patch.object(AuctionRepository, "_is_valid_status_change")
    @patch("mongoengine.queryset.QuerySet.update_one")
    @patch("mongoengine.queryset.QuerySet.first")
    def test_update_success(self, mock_first, mock_update, mock_valid_status):
        mock_first.return_value = self.test_auction
        mock_update.return_value = 1
        mock_valid_status.return_value = True

        result = self.repo.update(
            auction_id=self.mock_auction_id,
            user_role=UserRole.ADMIN.value,
            status=AuctionStatus.APPROVED.value
        )

        self.assertIsNotNone(result)
        mock_update.assert_called_once()

    @patch("mongoengine.queryset.QuerySet.first")
    def test_update_not_found(self, mock_first):
        mock_first.return_value = None

        with self.assertRaises(AuctionNotFoundException):
            self.repo.update(
                auction_id=self.mock_auction_id,
                user_role=UserRole.ADMIN.value,
                status=AuctionStatus.APPROVED.value
            )

    @patch("mongoengine.queryset.QuerySet.first")
    def test_update_invalid_status(self, mock_first):
        mock_first.return_value = self.test_auction

        with self.assertRaises(InvalidAuctionStateException):
            self.repo.update(
                auction_id=self.mock_auction_id,
                user_role=UserRole.ADMIN.value,
                status="invalid_status"
            )

    @patch.object(Auction, 'delete')
    @patch("mongoengine.queryset.QuerySet.first")
    def test_delete_success(self, mock_first, mock_delete):
        mock_first.return_value = self.test_auction

        result = self.repo.delete(
            auction_id=self.mock_auction_id,
            user_role=UserRole.ADMIN.value
        )

        self.assertTrue(result)
        mock_delete.assert_called_once()

    @patch("mongoengine.queryset.QuerySet.first")
    def test_delete_not_found(self, mock_first):
        mock_first.return_value = None

        with self.assertRaises(AuctionNotFoundException):
            self.repo.delete(
                auction_id=self.mock_auction_id,
                user_role=UserRole.ADMIN.value
            )

    @patch("mongoengine.queryset.QuerySet.count")
    def test_count(self, mock_count):
        mock_count.return_value = 5
        result = self.repo.count()
        self.assertEqual(result, 5)


if __name__ == '__main__':
    unittest.main()