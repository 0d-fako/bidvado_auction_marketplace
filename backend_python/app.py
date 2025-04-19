from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient


from src.bidvado.auth import auth_blueprint
from src.bidvado.controllers.auctions import auctions_blueprint
from src.bidvado.controllers.bids import bids_blueprint


app = Flask(__name__)


CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


app.config["JWT_SECRET_KEY"] = "your_secret_key"  # Replace with a secure key
jwt = JWTManager(app)


mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["bidvado_db"]


app.register_blueprint(auth_blueprint, url_prefix="/api/auth")
app.register_blueprint(auctions_blueprint, url_prefix="/api/auctions")
app.register_blueprint(bids_blueprint, url_prefix="/api/bids")


if __name__ == "__main__":
    app.run(debug=True)