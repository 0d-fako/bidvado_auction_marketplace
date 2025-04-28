from flask import Blueprint, request, jsonify
from datetime import datetime

from ..services.auction_service_impl import AuctionService
from ..utils.jwt_handler import JWTManager
from ..dtos.auction_dto import CreateAuctionRequest
from ..data.models.enum.enums import AuctionStatus
from ..exceptions.auction_exceptions import AuctionNotFoundException, InvalidAuctionStateException
from ..exceptions.auth_exceptions import NoSuchUserException, InvalidActionException


def init_auction_routes(auction_service: AuctionService, jwt_manager: JWTManager):
    auction_bp = Blueprint('auction', __name__, url_prefix='/api/auctions')

    @auction_bp.route('', methods=['POST'])
    @jwt_manager.token_required
    def create_auction(user_id):
        try:
            data = request.json

            try:
                start_time = datetime.fromisoformat(data.get('start_time'))
                end_time = datetime.fromisoformat(data.get('end_time'))
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400

            auction_request = CreateAuctionRequest(
                title=data.get('title'),
                seller_id=user_id,  # Use authenticated user as seller
                starting_bid=float(data.get('starting_bid', 0)),
                bid_increment=float(data.get('bid_increment', 0)),
                start_time=start_time,
                end_time=end_time,
                description=data.get('description'),
                images=data.get('images', [])
            )


            if not auction_request.title or auction_request.starting_bid <= 0 or auction_request.bid_increment <= 0:
                return jsonify({'error': 'Title, valid starting bid, and bid increment are required'}), 400

            auction = auction_service.create_auction(auction_request)


            return jsonify(auction.__dict__), 201
        except NoSuchUserException as e:
            return jsonify({'error': str(e)}), 404
        except InvalidActionException as e:
            return jsonify({'error': str(e)}), 403
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auction_bp.route('', methods=['GET'])
    def get_auctions():
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 10))
            status_param = request.args.get('status')


            status = None
            if status_param:
                try:
                    status = next(s for s in AuctionStatus if s.value == status_param)
                except StopIteration:
                    valid_statuses = [s.value for s in AuctionStatus]
                    return jsonify({
                        'error': f"Invalid status. Valid statuses are: {', '.join(valid_statuses)}"
                    }), 400


            auctions = auction_service.get_auctions(page, page_size, status)


            return jsonify([auction.__dict__ for auction in auctions]), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auction_bp.route('/<auction_id>', methods=['GET'])
    def get_auction(auction_id):
        try:
            auction = auction_service.get_auction(auction_id)
            if not auction:
                return jsonify({'error': 'Auction not found'}), 404

            return jsonify(auction.__dict__), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auction_bp.route('/<auction_id>', methods=['PUT'])
    @jwt_manager.token_required
    def update_auction(user_id, auction_id):
        try:
            data = request.json


            is_valid, user_id, role = jwt_manager.verify_token(jwt_manager._extract_token())

            update_data = {}
            allowed_fields = ['title', 'description', 'starting_bid', 'bid_increment', 'end_time', 'images']

            for field in allowed_fields:
                if field in data:
                    if field == 'end_time':
                        try:
                            update_data[field] = datetime.fromisoformat(data[field])
                        except ValueError:
                            return jsonify(
                                {'error': f'Invalid {field} format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
                    else:
                        update_data[field] = data[field]

            # Update auction
            updated_auction = auction_service.update_auction(auction_id, user_id, role, update_data)
            if not updated_auction:
                return jsonify({'error': 'Auction not found or update failed'}), 404

            return jsonify(updated_auction.__dict__), 200
        except AuctionNotFoundException as e:
            return jsonify({'error': str(e)}), 404
        except InvalidActionException as e:
            return jsonify({'error': str(e)}), 403
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auction_bp.route('/<auction_id>/approve', methods=['PATCH'])
    @jwt_manager.role_required('admin')
    def approve_auction(user_id, auction_id):
        """
        Approve an auction (admin only)
        """
        try:
            updated_auction = auction_service.approve_auction(auction_id, user_id)
            if not updated_auction:
                return jsonify({'error': 'Auction not found or approval failed'}), 404

            return jsonify(updated_auction.__dict__), 200
        except InvalidActionException as e:
            return jsonify({'error': str(e)}), 403
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @auction_bp.route('/<auction_id>/cancel', methods=['PATCH'])
    @jwt_manager.token_required
    def cancel_auction(user_id, auction_id):
        """
        Cancel an auction
        """
        try:
            # Get user role from token
            _, _, role = jwt_manager.verify_token(jwt_manager._extract_token())

            # Cancel auction
            success = auction_service.cancel_auction(auction_id, user_id, role)
            if not success:
                return jsonify({'error': 'Auction not found or cancellation failed'}), 404

            return jsonify({'message': 'Auction cancelled successfully'}), 200
        except AuctionNotFoundException as e:
            return jsonify({'error': str(e)}), 404
        except InvalidActionException as e:
            return jsonify({'error': str(e)}), 403
        except InvalidAuctionStateException as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return auction_bp