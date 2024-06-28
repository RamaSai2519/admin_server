from Utils.Services.ExpertService import ExpertService
from flask_jwt_extended import jwt_required
from flask import Blueprint

expert_routes = Blueprint("expert_routes", __name__)


@expert_routes.route("/admin/expert/experts/<string:id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_expert_route(id):
    return ExpertService.handle_expert(id)


@expert_routes.route("/admin/expert/create", methods=["POST"])
@jwt_required()
def create_expert_route():
    return ExpertService.create_expert()


@expert_routes.route("/admin/expert/callStream")
def call_stream_route():
    return ExpertService.call_stream()


@expert_routes.route("/admin/expert/popupData/<string:expertId>", methods=["GET"])
def get_popup_data_route(expertId):
    return ExpertService.get_popup_data(expertId)
