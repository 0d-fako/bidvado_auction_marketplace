import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from bson import ObjectId

from bidvado.data.repositories.user_repository import UserRepository
from bidvado.data.models.user import User
from bidvado.exceptions.auth_exceptions import UserAlreadyExistsException, NoSuchUserException


# from .bidvado.data.repositories.user_repository import UserRepository
# from your_app.models.user import User
# from your_app.exceptions.auth_exceptions import UserAlreadyExistsException, NoSuchUserException
#

class TestUserRepository(unittest.TestCase):
    def setUp(self):
        self.repo = UserRepository()
        self.mock_user_id = str(ObjectId())
        self.sample_time = datetime.now()

        # Sample test data
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

    @patch.object(User.objects, 'first')
    def test_create_user_success(self, mock_first):
        mock_first.return_value = None  # No existing user
        mock_save = MagicMock(return_value=self.test_user)
        User.save = mock_save

        result = self.repo.create(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password',
            role='bidder'
        )

        self.assertEqual(result, self.mock_user_id)
        mock_save.assert_called_once()

    @patch.object(User.objects, 'first')
    def test_create_user_exists(self, mock_first):
        mock_first.return_value = self.test_user

        with self.assertRaises(UserAlreadyExistsException):
            self.repo.create(
                username='testuser',
                email='test@example.com',
                password_hash='hashed_password',
                role='bidder'
            )

    @patch.object(User.objects, 'first')
    def test_find_by_id_found(self, mock_first):
        mock_first.return_value = self.test_user
        result = self.repo.find_by_id(self.mock_user_id)
        self.assertEqual(result.id, self.mock_user_id)

    @patch.object(User.objects, 'first')
    def test_find_by_id_not_found(self, mock_first):
        mock_first.return_value = None
        result = self.repo.find_by_id(self.mock_user_id)
        self.assertIsNone(result)

    @patch.object(User.objects, 'first')
    def test_find_by_email_found(self, mock_first):
        mock_first.return_value = self.test_user
        result = self.repo.find_by_email('test@example.com')
        self.assertEqual(result.email, 'test@example.com')

    @patch.object(User, 'update')
    @patch.object(User.objects, 'first')
    def test_update_user_success(self, mock_first, mock_update):
        mock_first.return_value = self.test_user

        result = self.repo.update(
            self.mock_user_id,
            username='newname',
            profile_picture='new.jpg'
        )

        self.assertTrue(result)
        mock_update.assert_called_once()

    @patch.object(User.objects, 'first')
    def test_update_user_not_found(self, mock_first):
        mock_first.return_value = None

        with self.assertRaises(NoSuchUserException):
            self.repo.update(self.mock_user_id, username='newname')

    @patch.object(User, 'delete')
    @patch.object(User.objects, 'first')
    def test_delete_user_success(self, mock_first, mock_delete):
        mock_first.return_value = self.test_user
        result = self.repo.delete(self.mock_user_id)
        self.assertTrue(result)
        mock_delete.assert_called_once()

    @patch.object(User.objects, 'first')
    def test_delete_user_not_found(self, mock_first):
        mock_first.return_value = None
        result = self.repo.delete(self.mock_user_id)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()