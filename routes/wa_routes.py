from Utils.Services.WAService import WAService
from flask_jwt_extended import jwt_required
from flask import Blueprint

wa_routes = Blueprint("wa_routes", __name__)
wa_service = WAService()


@wa_routes.route("/admin/wa/wahistory", methods=["GET"])
@jwt_required()
def get_wa_history_route():
    return wa_service.get_wa_history()


@wa_routes.route("/admin/wa/feedbacks", methods=["GET"])
@jwt_required()
def get_feedbacks_route():
    return wa_service.get_feedbacks()


@wa_routes.route("/admin/wa/templates", methods=["GET"])
@jwt_required()
def get_templates_route():
    return wa_service.get_templates()


@wa_routes.route("/admin/wa/send", methods=["POST"])
@jwt_required()
def send_message_route():
    return wa_service.handle_send()


@wa_routes.route("/admin/wa/preview", methods=["POST"])
@jwt_required()
def preview_message_route():
    return wa_service.get_preview()


@wa_routes.route("/admin/wa/proNum", methods=["GET"])
@jwt_required()
def get_pro_num_route():
    return wa_service.fetchStatus()
