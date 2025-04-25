from flask import Blueprint, request, jsonify
from src.bidvado.services.interfaces.auction_service import IAuctionService
from src.bidvado.dtos.auction_dto import CreateAuctionRequest
from src.bidvado.exceptions.auction_exceptions import AuctionNotFoundException, UnauthorizedException

def auction_bp(auction_service: IAuctionService):

    auction = Blueprint("auction", __name__)

    @auction.route("/create", methods=["POST"])
    def create_auction():
        try:
            data = request.json
            if not data:
                return jsonify({"error": "Invalid input, JSON data required"}), 400

            create_auction_request = CreateAuctionRequest(
                title=data.get("title"),
                description=data.get("description"),
                starting_bid=data.get("starting_bid"),
                end_time=data.get("end_time"),
                seller_id=data.get("seller_id"),
            )

            response = auction_service.create_auction(create_auction_request)
            return jsonify(response.__dict__), 201

        except Exception as e:
            return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    @auction.route("/<auction_id>", methods=["GET"])
    def get_auction(auction_id):
        """
        Retrieve details of a specific auction by ID.
        """
        try:
            response = auction_service.get_auction(auction_id)
            if not response:
                return jsonify({"error": "Auction not found"}), 404

            return jsonify(response.__dict__), 200

        except Exception as e:
            return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    @auction.route("/", methods=["GET"])
    def get_auctions():
        """
        Retrieve a paginated list of auctions.
        Accepts optional query parameters:
        - page (default: 1)
        - page_size (default: 10)
        - status (optional)
        """
        try:
            page = int(request.args.get("page", 1))
            page_size = int(request.args.get("page_size", 10))
            status = request.args.get("status", None)

            response = auction_service.get_auctions(page=page, page_size=page_size, status=status)
            return jsonify([auction.__dict__ for auction in response]), 200

        except Exception as e:
            return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    return auction