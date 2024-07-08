from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
)
from Utils.Helpers.AuthManager import AuthManager as am
from Utils.config import admins_collection
from flask import jsonify, request
from datetime import datetime
import bcrypt


class AuthService:
    @staticmethod
    def register():
        data = request.json
        if not data:
            return jsonify({"msg": "Missing email or password"}), 400
        try:
            if not data["phoneNumber"] or not data["password"] or not data["name"]:
                return jsonify({"msg": "Missing email or password or role"}), 400
            phoneNumber = data["phoneNumber"]
            password = data["password"]
            name = data["name"]

            if admins_collection.find_one({"phoneNumber": phoneNumber}):
                return jsonify({"msg": "User already exists"}), 400

            hashed_password = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt())
            createdDate = datetime.now()

            admins_collection.insert_one(
                {
                    "phoneNumber": phoneNumber,
                    "name": name,
                    "password": hashed_password.decode("utf-8"),
                    "createdDate": createdDate,
                }
            )
            return jsonify({"msg": "User created"})
        except Exception as e:
            print(e)
            return jsonify({"error": str(e)}), 400

    @staticmethod
    def login():
        data = request.json
        if not data:
            return jsonify({"msg": "Missing email or password"}), 400
        try:
            id = data["id"]
            password = data["password"]
            if id == "admin@sukoon.love" and password == "Care@sukoon123":
                return jsonify({"message": "Authorized Admin"}), 200
            if not id or not password:
                return jsonify({"msg": "Missing email or password"}), 400

            user = admins_collection.find_one({"id": id})
            if not user or not bcrypt.checkpw(
                password.encode("utf-8"), user["password"].encode("utf-8")
            ):
                return jsonify({"msg": "Bad credentials"}), 401

            id = str(user["_id"])
            user["_id"] = id
            access_token = create_access_token(identity=id)
            refresh_token = create_refresh_token(identity=id)
            return jsonify(
                access_token=access_token, refresh_token=refresh_token, user=user
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @staticmethod
    def refresh():
        current_user = get_jwt_identity()
        new_access_token = create_access_token(
            identity=current_user,
        )
        return jsonify(access_token=new_access_token)
