from flask import request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
)
from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf


class AuthService:
    @staticmethod
    def login():
        if not request.is_json:
            return jsonify({"msg": "Missing JSON in request"}), 400

        username = request.json.get("username", None)
        password = request.json.get("password", None)
        if not username or not password:
            return jsonify({"msg": "Missing username or password"}), 400

        user = uf.authenticate(username, password)
        if not user:
            return jsonify({"msg": "Bad username or password"}), 401

        access_token = create_access_token(identity=user["id"])
        refresh_token = create_refresh_token(identity=user["id"])

        resp = make_response(jsonify({"msg": "Login successful"}), 200)
        resp.set_cookie(
            "access_token", access_token, httponly=True, secure=True, samesite="Strict"
        )
        resp.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
            secure=True,
            samesite="Strict",
        )
        return resp

    @staticmethod
    def refresh():
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)

        resp = make_response(jsonify({"msg": "Token refreshed"}), 200)
        resp.set_cookie(
            "access_token", access_token, httponly=True, secure=True, samesite="Strict"
        )

        return resp

    @staticmethod
    def logout():
        resp = make_response(jsonify({"msg": "Logout successful"}), 200)
        resp.delete_cookie("access_token")
        resp.delete_cookie("refresh_token")
        return resp

    @staticmethod
    def protected():
        current_user_id = get_jwt_identity()
        return jsonify(logged_in_as=current_user_id), 200
