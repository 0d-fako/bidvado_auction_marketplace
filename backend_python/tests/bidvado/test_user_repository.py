import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from bson import ObjectId


from src.bidvado.data.models.user import User
from src.bidvado.exceptions.auth_exceptions import UserAlreadyExistsException, NoSuchUserException

from src.bidvado.data.repositories.user_repository import UserRepository
from mongoengine import connect

connect(db="test_bidvado_db", host="mongodb://localhost:27017/")

# from .bidvado.data.repositories.user_repository import UserRepository


class TestUserRepository(unittest.TestCase):
    def setUp(self):
        self.repo = UserRepository()
        self.mock_user_id = str(ObjectId())
        self.sample_time = datetime.now()

        self.test_user_data = {
            'id': self.mock_user_id,
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'hashed_password',
            'role': 'bidder',
            'created_at': self.sample_time,
            'updated_at': self.sample_time
        }

        self.test_user = User(**self.test_user_data)

    @patch.object(User, 'save', autospec=True)
    @patch("mongoengine.queryset.QuerySet.first")
    def test_create_user_success(self, mock_first, mock_save):
        mock_first.return_value = None
        mock_save.return_value = self.test_user

        result = self.repo.create(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password',
            role='bidder'
        )

        self.assertEqual(result, self.mock_user_id)
        mock_save.assert_called_once()

    @patch("mongoengine.queryset.QuerySet.first")
    def test_create_user_exists(self, mock_first):
        mock_first.return_value = self.test_user

        with self.assertRaises(UserAlreadyExistsException):
            self.repo.create(
                username='testuser',
                email='test@example.com',
                password_hash='hashed_password',
                role='bidder'
            )

    @patch("mongoengine.queryset.QuerySet.first")
    def test_find_by_id_found(self, mock_first):
        mock_first.return_value = self.test_user
        result = self.repo.find_by_id(self.mock_user_id)
        self.assertEqual(str(result.id), self.mock_user_id)


    @patch("mongoengine.queryset.QuerySet.first")
    def test_find_by_id_not_found(self, mock_first):
        mock_first.return_value = None
        result = self.repo.find_by_id(self.mock_user_id)
        self.assertIsNone(result)

    @patch("mongoengine.queryset.QuerySet.first")
    def test_find_by_email_found(self, mock_first):
        mock_first.return_value = self.test_user
        result = self.repo.find_by_email('test@example.com')
        self.assertEqual(result.email, 'test@example.com')

    @patch("mongoengine.queryset.QuerySet.update")
    @patch("mongoengine.queryset.QuerySet.first")
    def test_update_user_success(self, mock_first, mock_update):
        mock_first.return_value = self.test_user  # Simulate found user

        result = self.repo.update(
            self.mock_user_id,
            username="newname",
            profile_picture="new.jpg"
        )

        self.assertTrue(result)
        mock_update.assert_called_once()

    @patch("mongoengine.queryset.QuerySet.first")
    def test_update_user_not_found(self, mock_first):
        mock_first.return_value = None

        with self.assertRaises(NoSuchUserException):
            self.repo.update(self.mock_user_id, username='newname')

    @patch("mongoengine.queryset.QuerySet.delete")
    @patch("mongoengine.queryset.QuerySet.first")
    def test_delete_user_success(self, mock_first, mock_delete):
        mock_first.return_value = self.test_user
        result = self.repo.delete(self.mock_user_id)
        self.assertTrue(result)
        mock_delete.assert_called_once()

    @patch("mongoengine.queryset.QuerySet.first")
    def test_delete_user_not_found(self, mock_first):
        mock_first.return_value = None
        with self.assertRaises(NoSuchUserException) as context:
            self.repo.delete(self.mock_user_id)

        self.assertEqual(str(context.exception), "User not found.")


if __name__ == '__main__':
    unittest.main()