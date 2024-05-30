import bcrypt
from Utils.config import admins_collection
from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
)
from datetime import datetime


class AuthService:
    @staticmethod
    def register():
        username = request.json.get("email", None)
        password = request.json.get("password", None)

        if not username or not password:
            return jsonify({"msg": "Missing email or password"}), 400

        if admins_collection.find_one({"email": username}):
            return jsonify({"msg": "User already exists"}), 400

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        createdDate = datetime.now()

        admins_collection.insert_one(
            {
                "email": username,
                "password": hashed_password.decode("utf-8"),
                "createdDate": createdDate,
                "role": "admin",
            }
        )
        return jsonify({"msg": "User created"})

    @staticmethod
    def login():
        email = request.json.get("email", None)
        password = request.json.get("password", None)
        if not email or not password:
            return jsonify({"msg": "Missing email or password"}), 400

        user = admins_collection.find_one({"email": email})
        if not user or not bcrypt.checkpw(
            password.encode("utf-8"), user["password"].encode("utf-8")
        ):
            return jsonify({"msg": "Bad credentials"}), 401

        id = str(user["_id"])
        access_token = create_access_token(identity=id)
        refresh_token = create_refresh_token(identity=id)
        return jsonify(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    def refresh():
        current_user = get_jwt_identity()
        new_access_token = create_access_token(
            identity=current_user,
        )
        return jsonify(access_token=new_access_token)
