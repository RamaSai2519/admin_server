from Utils.Helpers.InsightsManager import InsightsManager
from Utils.Services.AppService import AppService
from flask_jwt_extended import jwt_required
from flask import Blueprint

service_routes = Blueprint("service_routes", __name__)


@service_routes.route("/admin/service/schedule/<id>", methods=["PUT", "DELETE", "GET"])
@jwt_required()
def update_schedule_route(id):
    return AppService.update_schedule(id)


@service_routes.route("/admin/service/approve/<string:id>/<level>", methods=["PUT"])
@jwt_required()
def approve_user(id, level):
    return AppService.approve_application(id, level)


@service_routes.route("/admin/service/save-fcm-token", methods=["POST"])
@jwt_required()
def save_fcm_token_route():
    return AppService.save_fcm_token()


@service_routes.route("/admin/service/dashboardstats")
@jwt_required()
def get_dashboard_stats_route():
    return InsightsManager.get_dashboard_stats()


@service_routes.route("/admin/service/callinsights")
@jwt_required()
def get_call_insights_route():
    return AppService.get_insights()


@service_routes.route("/admin/service/upload", methods=["POST"])
def upload_route():
    return AppService.upload()
