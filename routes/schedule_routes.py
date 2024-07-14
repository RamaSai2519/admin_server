from Utils.Services.ScheduleService import ScheduleService
from flask_jwt_extended import jwt_required
from flask import Blueprint

schedule_routes = Blueprint("schedule_routes", __name__)


@schedule_routes.route("/admin/data/schedules", methods=["POST", "GET"])
def schedules_route():
    return ScheduleService.schedules()


@schedule_routes.route("/admin/data/slots", methods=["POST"])
def slots_route():
    return ScheduleService.get_slots()
