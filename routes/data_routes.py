from Utils.Services.DataService import DataService
from flask_jwt_extended import jwt_required
from flask import Blueprint

data_routes = Blueprint("data_routes", __name__)

data_service = DataService()


@data_routes.route("/admin/data/errorlogs")
@jwt_required()
def get_error_logs_route():
    return data_service.get_error_logs()


@data_routes.route("/admin/data/calls")
@jwt_required()
def get_calls_route():
    return data_service.get_all_calls()


@data_routes.route("/admin/data/applications")
@jwt_required()
def get_applications_route():
    return data_service.get_applications()


@data_routes.route("/admin/data/users")
@jwt_required()
def get_users_route():
    return data_service.get_users()


@data_routes.route("/admin/data/experts")
@jwt_required()
def get_experts_route():
    return data_service.get_experts()


@data_routes.route("/admin/data/categories", methods=["GET", "POST"])
@jwt_required()
def get_categories_route():
    return data_service.get_categories()


@data_routes.route("/admin/data/timings", methods=["GET", "POST"])
@jwt_required()
def timings_route():
    return data_service.get_timings()


@data_routes.route("/admin/data/userCities", methods=["GET"])
@jwt_required()
def user_cities_route():
    return data_service.get_cities()
