from flask import Blueprint, request, jsonify

from ..utils.jwt_handler import JWTManager
from ..services.bid_service_impl import BidService
from ..dtos.bid_dto import PlaceBidRequest
from ..exceptions.bid_exceptions import InvalidBidException, AuctionClosedException
from ..exceptions.auction_exceptions import AuctionNotFoundException
from ..exceptions.auth_exceptions import NoSuchUserException


def init_bid_routes(bid_service: BidService, jwt_manager: JWTManager):
    bid_bp = Blueprint('bid', __name__, url_prefix='/api/bids')

    @bid_bp.route('', methods=['POST'])
    @jwt_manager.token_required
    def place_bid(user_id):

        try:
            data = request.json

            if 'auction_id' not in data or 'amount' not in data:
                return jsonify({'error': 'auction_id and amount are required'}), 400

            try:
                amount = float(data['amount'])
                if amount <= 0:
                    return jsonify({'error': 'Amount must be greater than zero'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Amount must be a valid number'}), 400

            bid_request = PlaceBidRequest(
                auction_id=data['auction_id'],
                bidder_id=user_id,
                amount=amount
            )


            response = bid_service.place_bid(bid_request)

            return jsonify(response.__dict__), 201
        except InvalidBidException as e:
            return jsonify({'error': str(e)}), 400
        except AuctionClosedException as e:
            return jsonify({'error': str(e)}), 400
        except AuctionNotFoundException as e:
            return jsonify({'error': str(e)}), 404
        except NoSuchUserException as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bid_bp.route('/<bid_id>', methods=['GET'])
    def get_bid(bid_id):
        try:
            bid = bid_service.get_bid(bid_id)
            if not bid:
                return jsonify({'error': 'Bid not found'}), 404

            return jsonify(bid.__dict__), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bid_bp.route('/auction/<auction_id>', methods=['GET'])
    def get_auction_bids(auction_id):
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 10))

            bids = bid_service.get_auction_bids(auction_id, page, page_size)

            return jsonify([bid.__dict__ for bid in bids]), 200
        except AuctionNotFoundException as e:
            return jsonify({'error': str(e)}), 404
        except ValueError as e:
            return jsonify({'error': 'Invalid page or pageSize parameter'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bid_bp.route('/auction/<auction_id>/highest', methods=['GET'])
    def get_highest_bid(auction_id):

        try:
            bid = bid_service.get_highest_bid(auction_id)
            if not bid:
                return jsonify({}), 200

            return jsonify(bid.__dict__), 200
        except AuctionNotFoundException as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bid_bp.route('/user/<user_id>', methods=['GET'])
    @jwt_manager.token_required
    def get_user_bids(user_id, requesting_user_id):

        try:
            is_valid, user_id, role = jwt_manager.verify_token(jwt_manager._extract_token())

            if user_id != requesting_user_id and role != 'admin':
                return jsonify({'error': 'Unauthorized to view other users bids'}), 403

            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 10))

            bids = bid_service.get_user_bids(user_id, page, page_size)

            return jsonify([bid.__dict__ for bid in bids]), 200
        except NoSuchUserException as e:
            return jsonify({'error': str(e)}), 404
        except ValueError as e:
            return jsonify({'error': 'Invalid page or pageSize parameter'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return bid_bp