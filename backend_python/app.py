from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import os
from dotenv import load_dotenv
from mongoengine import connect

from src.bidvado.data.repositories.user_repository import UserRepository
from src.bidvado.data.repositories.auction_repository import AuctionRepository
from src.bidvado.data.repositories.bid_repository import BidRepository
from src.bidvado.utils.jwt_handler import JWTManager
from src.bidvado.services.auth_service_impl import AuthService
from src.bidvado.services.auction_service_impl import AuctionService
from src.bidvado.services.bid_service_impl import BidService
from src.bidvado.websockets.websocket_handler import WebSocketHandler
from src.bidvado.controllers.auth_controller import init_auth_routes
from src.bidvado.controllers.auction_controller import init_auction_routes
from src.bidvado.controllers.bid_controller import init_bid_routes


load_dotenv()


def setup_mongodb():
    """Connect to MongoDB"""
    db_host = os.getenv('MONGODB_HOST', 'localhost')
    db_port = int(os.getenv('MONGODB_PORT', '27017'))
    db_name = os.getenv('MONGODB_DB', 'bidvado')

    connect(db=db_name, host=f"mongodb://{db_host}:{db_port}/{db_name}")


def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret_key')

    # Connect to MongoDB
    setup_mongodb()

    # Set up CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Initialize websocket handler
    websocket_handler = WebSocketHandler(socketio)

    # Initialize repositories
    user_repository = UserRepository()
    auction_repository = AuctionRepository()
    bid_repository = BidRepository()

    # Initialize JWT manager
    jwt_manager = JWTManager(user_repository)


    auth_service = AuthService(
        user_repository=user_repository,
        jwt_manager=jwt_manager
    )

    auction_service = AuctionService(
        auction_repository=auction_repository,
        user_repository=user_repository
    )

    bid_service = BidService(
        bid_repository=bid_repository,
        auction_repository=auction_repository,
        user_repository=user_repository,
        notification_service=None,
        websocket_handler=websocket_handler
    )

    # Register blueprints
    app.register_blueprint(init_auth_routes(auth_service))
    app.register_blueprint(init_auction_routes(auction_service, jwt_manager))
    app.register_blueprint(init_bid_routes(bid_service))

    return app, socketio


if __name__ == "__main__":
    app, socketio = create_app()
    port = int(os.getenv('PORT', 5000))

    # Run the app
    socketio.run(app, host='0.0.0.0', port=port, debug=True)