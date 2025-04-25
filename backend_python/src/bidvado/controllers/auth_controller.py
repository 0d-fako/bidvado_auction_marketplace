from flask import Blueprint, request, jsonify
from src.bidvado.services.auth_service_impl import AuthService
from src.bidvado.data.repositories.user_repository import UserRepository
from src.bidvado.dtos.user_dto import UserRegisterRequest, UserLoginRequest
from src.bidvado.exceptions.auth_exceptions import (
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UserCreationException,
)

auth_service = AuthService(UserRepository())

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid input, JSON data required"}), 400

        request_dto = UserRegisterRequest(
            username=data.get("username"),
            email=data.get("email"),
            password=data.get("password"),
            role=data.get("role"),
        )

        response = auth_service.register(request_dto)
        return jsonify(response.__dict__), 201

    except UserAlreadyExistsException as e:
        return jsonify({"error": str(e)}), 409
    except UserCreationException as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid input, JSON data required"}), 400

        request_dto = UserLoginRequest(
            username=data.get("email"),
            password=data.get("password"),
        )

        response = auth_service.login(request_dto)
        return jsonify(response.__dict__), 200

    except InvalidCredentialsException as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500