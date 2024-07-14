from Utils.Services.WAService import WAService
from flask_jwt_extended import jwt_required
from flask import Blueprint

wa_routes = Blueprint("wa_routes", __name__)

@wa_routes.route("/admin/wa/wahistory", methods=["GET"])
@jwt_required()
def get_wa_history_route():
    return WAService.get_wa_history()


@wa_routes.route("/admin/wa/feedbacks", methods=["GET"])
@jwt_required()
def get_feedbacks_route():
    return WAService.get_feedbacks()
