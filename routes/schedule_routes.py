from Utils.Services.ScheduleService import ScheduleService
from flask import Blueprint

schedule_routes = Blueprint("schedule_routes", __name__)


@schedule_routes.route("/admin/data/schedules", methods=["POST", "GET"])
def schedules_route():
    return ScheduleService.schedules()


@schedule_routes.route("/admin/data/slots", methods=["POST"])
def slots_route():
    return ScheduleService.get_slots()

@schedule_routes.route("/admin/data/newSchedules", methods=["GET"])
def test_route():
    return ScheduleService.get_dynamo_schedules()

@schedule_routes.route("/admin/data/schedule/<scheduleId>", methods=["DELETE"])
def delete_schedule_route(scheduleId):
    return ScheduleService.delete_schedule(scheduleId)