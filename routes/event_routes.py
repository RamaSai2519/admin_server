from Utils.Services.EventService import EventService
from flask_jwt_extended import jwt_required
from flask import Blueprint

event_routes = Blueprint("event_routes", __name__)


@event_routes.route("/admin/event/data", methods=["GET"])
@jwt_required()
def get_events_route():
    return EventService.get_events()


@event_routes.route("/admin/event/handle", methods=["GET", "PUT", "POST"])
@jwt_required()
def get_event_route():
    return EventService.handle_event_config()


@event_routes.route("/admin/event/users", methods=["GET"])
@jwt_required()
def get_users_by_event_route():
    return EventService.get_users_by_event()
