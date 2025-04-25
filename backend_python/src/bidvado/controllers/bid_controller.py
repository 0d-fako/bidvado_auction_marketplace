from flask import Blueprint, request, jsonify

from src.bidvado.utils.token_validator import token_required
from ..services.bid_service_impl import BidService
from ..dtos.bid_dto import PlaceBidRequest
from ..exceptions.bid_exceptions import InvalidBidException, AuctionClosedException
from ..exceptions.auction_exceptions import AuctionNotFoundException

bid_bp = Blueprint('bid', __name__, url_prefix='/api/bids')


def init_bid_routes(bid_service: BidService):
    @bid_bp.route('', methods=['POST'])
    @token_required
    def place_bid(user_id):
        data = request.json
        try:
            bid_request = PlaceBidRequest(
                auction_id=data['auction_id'],
                bidder_id=user_id,
                amount=float(data['amount'])
            )

            response = bid_service.place_bid(bid_request)
            return jsonify(response.__dict__), 201
        except KeyError as e:
            return jsonify({'error': f'Missing required field: {str(e)}'}), 400
        except (InvalidBidException, AuctionClosedException) as e:
            return jsonify({'error': str(e)}), 400
        except AuctionNotFoundException as e:
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
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @bid_bp.route('/auction/<auction_id>/highest', methods=['GET'])
    def get_highest_bid(auction_id):
        try:
            bid = bid_service.get_highest_bid(auction_id)
            if not bid:
                return jsonify({}), 200  # No bids yet
            return jsonify(bid.__dict__), 200
        except AuctionNotFoundException as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return bid_bp