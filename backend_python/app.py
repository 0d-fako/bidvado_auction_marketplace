from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import os
from dotenv import load_dotenv

from src.bidvado.controllers.auth_controller import auth_bp
from src.bidvado.controllers.auction_controller import auction_bp
from src.bidvado.controllers.bid_controller import bid_bp
from src.bidvado.data.repositories.user_repository import UserRepository
from src.bidvado.data.repositories.auction_repository import AuctionRepository
from src.bidvado.data.repositories.bid_repository import BidRepository
from src.bidvado.services.auth_service_impl import AuthService
from src.bidvado.services.auction_service_impl import AuctionService
from src.bidvado.services.bid_service_impl import BidService
from src.bidvado.websockets.event_emitter import EventEmitter


load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret_key')

    CORS(app)

    socketio = SocketIO(app, cors_allowed_origins="*")


    user_repository = UserRepository()
    auction_repository = AuctionRepository()
    bid_repository = BidRepository()


    auth_service = AuthService(user_repository, app.config['SECRET_KEY'])
    auction_service = AuctionService(auction_repository, user_repository)
    event_emitter = EventEmitter(socketio)
    bid_service = BidService(
        bid_repository=bid_repository,
        auction_repository=auction_repository,
        user_repository=user_repository,
        notification_service=None,
        event_emitter=event_emitter
    )


    app.register_blueprint(auth_bp(auth_service), url_prefix='/auth')
    app.register_blueprint(auction_bp(auction_service), url_prefix='/auction')
    app.register_blueprint(bid_bp(bid_service), url_prefix='/bid')

    return app, socketio


if __name__ == "__main__":
    app, socketio = create_app()
    port = int(os.getenv('PORT', 5000))

    # Run the app with SocketIO support
    socketio.run(app, host='0.0.0.0', port=port, debug=True)