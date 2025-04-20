from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from bcrypt import hashpw, gensalt, checkpw
from pymongo import MongoClient


auth_blueprint = Blueprint("auth", __name__)


mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["bidvado_db"]
users_collection = db["users"]


@auth_blueprint.route("/register", methods=["POST"])
def register():
    data = request.json


    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password are required"}), 400


    if users_collection.find_one({"username": data["username"]}):
        return jsonify({"error": "Username already exists"}), 409


    hashed_password = hashpw(data["password"].encode("utf-8"), gensalt())
    new_user = {
        "username": data["username"],
        "password": hashed_password.decode("utf-8"),
        "user_type": data.get("user_type", "buyer")
    }
    users_collection.insert_one(new_user)
    return jsonify({"message": "User registered successfully!"}), 201


@auth_blueprint.route("/login", methods=["POST"])
def login():
    data = request.json

    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "Username and password are required"}), 400

    user = users_collection.find_one({"username": data["username"]})
    if not user or not checkpw(data["password"].encode("utf-8"), user["password"].encode("utf-8")):
        return jsonify({"error": "Invalid username or password"}), 401

    token = create_access_token(identity={"username": user["username"], "user_type": user["user_type"]})
    return jsonify({"token": token}), 200