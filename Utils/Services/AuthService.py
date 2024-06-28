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
            return jsonify({"msg": "Missing data"}), 400
        id = data["id"]
        name = data["name"]
        password = data["password"]
        role = data["role"]

        if not id or not password or not role:
            return jsonify({"msg": "Missing email or password or role"}), 400

        if admins_collection.find_one({"id": id}):
            return jsonify({"msg": "User already exists"}), 400

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt())
        createdDate = datetime.now()

        admins_collection.insert_one(
            {
                "id": id,
                "name": name,
                "password": hashed_password.decode("utf-8"),
                "createdDate": createdDate,
                "role": role,
            }
        )
        return jsonify({"msg": "User created"})

    @staticmethod
    def login():
        data = request.json
        if not data:
            return jsonify({"msg": "Missing data"}), 400
        id = data["id"]
        password = data["password"]
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

    @staticmethod
    def refresh():
        current_user = get_jwt_identity()
        new_access_token = create_access_token(
            identity=current_user,
        )
        return jsonify(access_token=new_access_token)
