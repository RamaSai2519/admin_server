from Utils.Services.DataService import DataService
from flask_jwt_extended import jwt_required
from flask import Blueprint

data_routes = Blueprint("data_routes", __name__)


@data_routes.route("/admin/data/errorlogs")
@jwt_required()
def get_error_logs_route():
    return DataService.get_error_logs()


@data_routes.route("/admin/data/calls")
@jwt_required()
def get_calls_route():
    return DataService.get_all_calls()


@data_routes.route("/admin/data/applications")
@jwt_required()
def get_applications_route():
    return DataService.get_applications()


@data_routes.route("/admin/data/users")
@jwt_required()
def get_users_route():
    return DataService.get_users()


@data_routes.route("/admin/data/experts")
@jwt_required()
def get_experts_route():
    return DataService.get_experts()


@data_routes.route("/admin/data/categories", methods=["GET", "POST"])
@jwt_required()
def get_categories_route():
    return DataService.get_categories()


@data_routes.route("/admin/data/schedules", methods=["POST", "GET"])
def schedules_route():
    return DataService.schedules()


@data_routes.route("/admin/data/slots", methods=["POST"])
def slots_route():
    return DataService.get_slots()


@data_routes.route("/admin/data/timings", methods=["GET", "POST"])
@jwt_required()
def timings_route():
    return DataService.get_timings()


@data_routes.route("/admin/data/wahistory", methods=["GET"])
@jwt_required()
def get_wa_history_route():
    return DataService.get_wa_history()


@data_routes.route("/admin/data/feedbacks", methods=["GET"])
@jwt_required()
def get_feedbacks_route():
    return DataService.get_feedbacks()
