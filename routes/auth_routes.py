from Utils.Services.AuthService import AuthService
from flask_jwt_extended import jwt_required
from flask import Blueprint

auth_routes = Blueprint("auth_routes", __name__)


@auth_routes.route("/admin/auth/login", methods=["POST"])
def login_route():
    return AuthService.login()


@auth_routes.route("/admin/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_route():
    return AuthService.refresh()


@auth_routes.route("/admin/auth/register", methods=["POST"])
def register_route():
    return AuthService.register()
