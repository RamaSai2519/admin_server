from Utils.Services.CallService import CallService
from flask_jwt_extended import jwt_required
from flask import Blueprint

call_routes = Blueprint("call_routes", __name__)


@call_routes.route("/admin/call/calls/<string:id>", methods=["GET", "PUT"])
@jwt_required()
def handle_call_route(id):
    return CallService.handle_call(id)


@call_routes.route("/admin/call/callUser", methods=["POST"])
def expert_call_user_route():
    return CallService.expert_call_user()


@call_routes.route("/admin/call/connect", methods=["POST"])
def connect_route():
    return CallService.connect()
