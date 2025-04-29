from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import os
from dotenv import load_dotenv
from mongoengine import connect

from src.bidvado.data.repositories.user_repository import UserRepository
from src.bidvado.data.repositories.auction_repository import AuctionRepository
from src.bidvado.data.repositories.bid_repository import BidRepository
from src.bidvado.data.repositories.notification_repository import NotificationRepository
from src.bidvado.utils.jwt_handler import JWTManager
from src.bidvado.services.auth_service_impl import AuthService
from src.bidvado.services.auction_service_impl import AuctionService
from src.bidvado.services.bid_service_impl import BidService
from src.bidvado.services.notification_service_impl import NotificationService
from src.bidvado.websockets.websocket_handler import WebSocketHandler
from src.bidvado.controllers.auth_controller import init_auth_routes
from src.bidvado.controllers.auction_controller import init_auction_routes
from src.bidvado.controllers.bid_controller import init_bid_routes
from src.bidvado.controllers.notification_controller import init_notification_routes


load_dotenv()


def setup_mongodb():
    db_host = os.getenv('MONGODB_HOST', 'localhost')
    db_port = int(os.getenv('MONGODB_PORT', '27017'))
    db_name = os.getenv('MONGODB_DB', 'bidvado')

    connect(db=db_name, host=f"mongodb://{db_host}:{db_port}/{db_name}")


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret_key')

    setup_mongodb()

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    socketio = SocketIO(app, cors_allowed_origins="*")

    websocket_handler = WebSocketHandler(socketio)

    user_repository = UserRepository()
    auction_repository = AuctionRepository()
    bid_repository = BidRepository()
    notification_repository = NotificationRepository()

    jwt_manager = JWTManager(user_repository)

    notification_service = NotificationService(
        notification_repository=notification_repository,
        auction_repository=auction_repository,
        user_repository=user_repository,
        bid_repository=bid_repository,
        websocket_handler=websocket_handler
    )

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
        notification_service=notification_service,
        websocket_handler=websocket_handler
    )


    app.register_blueprint(init_auth_routes(auth_service))
    app.register_blueprint(init_auction_routes(auction_service, jwt_manager))
    app.register_blueprint(init_bid_routes(bid_service))
    app.register_blueprint(init_notification_routes(notification_service, jwt_manager))


    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

    return app, socketio


if __name__ == "__main__":
    app, socketio = create_app()
    port = int(os.getenv('PORT', 5000))


    socketio.run(app, host='0.0.0.0', port=port, debug=True)