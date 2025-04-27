from flask import Blueprint, request, jsonify
from ..services.auth_service_impl import AuthService
from ..dtos.user_dto import UserRegisterRequest, UserLoginRequest
from ..exceptions.auth_exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    TokenVerificationException,
    UserCreationException
)
from ..data.models.enum.enums import UserRole


def init_auth_routes(auth_service: AuthService):
    auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

    @auth_bp.route('/register', methods=['POST'])
    def register():

        try:
            data = request.json

            role_str = data.get('role', 'bidder')
            try:
                role = next(r for r in UserRole if r.value == role_str)
            except StopIteration:
                valid_roles = [r.value for r in UserRole]
                return jsonify({
                    'error': f"Invalid role. Valid roles are: {', '.join(valid_roles)}"
                }), 400


            register_request = UserRegisterRequest(
                username=data.get('username'),
                email=data.get('email'),
                password=data.get('password'),
                role=role,
                profile_picture=data.get('profile_picture')
            )


            if not register_request.username or not register_request.email or not register_request.password:
                return jsonify({'error': 'Username, email, and password are required'}), 400

            user = auth_service.register(register_request)


            return jsonify(user.__dict__), 201
        except UserAlreadyExistsException as e:
            return jsonify({'error': str(e)}), 409
        except UserCreationException as e:
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auth_bp.route('/login', methods=['POST'])
    def login():
        try:
            data = request.json

            login_request = UserLoginRequest(
                email=data.get('email', ''),
                username=data.get('username', ''),
                password=data.get('password', '')
            )

            if not login_request.email or not login_request.password:
                return jsonify({'error': 'Email and password are required'}), 400

            user = auth_service.login(login_request)

            return jsonify(user.__dict__), 200
        except InvalidCredentialsException as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auth_bp.route('/verify', methods=['POST'])
    def verify_token():
        try:
            data = request.json
            token = data.get('token')

            if not token:
                return jsonify({'error': 'Token is required'}), 400

            is_valid, user_id = auth_service.validate_token(token)

            if is_valid and user_id:
                return jsonify({'valid': True, 'user_id': user_id}), 200
            else:
                return jsonify({'valid': False}), 401
        except TokenVerificationException as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auth_bp.route('/reset-password', methods=['POST'])
    def request_reset():
        try:
            data = request.json
            email = data.get('email')

            if not email:
                return jsonify({'error': 'Email is required'}), 400

            auth_service.request_password_reset(email)
            return jsonify({'message': 'Password reset instructions sent if email exists'}), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auth_bp.route('/reset-password/<token>', methods=['POST'])
    def reset_password(token):
        try:
            data = request.json
            new_password = data.get('password')

            if not new_password:
                return jsonify({'error': 'New password is required'}), 400

            success = auth_service.reset_password(token, new_password)

            if success:
                return jsonify({'message': 'Password updated successfully'}), 200
            else:
                return jsonify({'error': 'Invalid or expired reset token'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return auth_bp