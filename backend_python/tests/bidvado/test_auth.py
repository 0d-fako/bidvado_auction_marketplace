import unittest
from flask import Flask
from flask_jwt_extended import JWTManager
from unittest.mock import patch
from src.bidvado.auth import auth_blueprint

class TestAuth(unittest.TestCase):
    def setUp(self):
        # Setup Flask app for testing
        self.app = Flask(__name__)
        self.app.config["JWT_SECRET_KEY"] = "test_secret_key"
        self.app.register_blueprint(auth_blueprint, url_prefix="/api/auth")
        self.client = self.app.test_client()

    @patch("src.bidvado.auth.users_collection")
    def test_register_user_success(self, mock_users_collection):
        # Mock MongoDB insert_one
        mock_users_collection.insert_one.return_value = None

        response = self.client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "testpassword"
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {"message": "User registered successfully!"})

    @patch("src.bidvado.auth.users_collection")
    def test_login_user_success(self, mock_users_collection):
        # Mock MongoDB find_one
        mock_users_collection.find_one.return_value = {
            "username": "testuser",
            "password": "testpassword"
        }

        response = self.client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpassword"
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.json)

    @patch("src.bidvado.auth.users_collection")
    def test_login_user_failure(self, mock_users_collection):
        # Mock MongoDB find_one to return None
        mock_users_collection.find_one.return_value = None

        response = self.client.post("/api/auth/login", json={
            "username": "unknownuser",
            "password": "wrongpassword"
        })

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json, {"error": "Invalid credentials"})


