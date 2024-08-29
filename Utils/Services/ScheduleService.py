from pprint import pprint
from bson import ObjectId
from datetime import datetime
from flask import jsonify, request
from Utils.Classes.Slot import Slot
from Utils.Classes.Schedule import Schedule
from Utils.Services.GQLClient import call_graphql
from Utils.Helpers.FormatManager import FormatManager as fm
from Utils.Helpers.ScheduleManager import ScheduleManager as sm
from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from Utils.config import schedules_collection, experts_collection, users_collection


class ScheduleService:
    @staticmethod
    def schedules():
        if request.method == "GET":
            return ScheduleService.get_schedules()
        elif request.method == "POST":
            return ScheduleService.create_schedule()
        else:
            return jsonify({"error": "Invalid request method"}), 404

    @staticmethod
    def get_schedules():
        size, offset, page = uf.pagination_helper()
        schedules = list(schedules_collection.find({}, {
            "lastModifiedBy": 0
        }).sort("datetime", -1).skip(offset).limit(size))

        total_schedules = schedules_collection.count_documents({})
        schedules = uf.format_schedules(schedules)
        return jsonify({
            "data": schedules,
            "total": total_schedules
        })

    @staticmethod
    def create_schedule():
        data = dict(request.json) if request.json is not None else {}
        if not data:
            return jsonify({"error": "Invalid request data"}), 400

        schedule = Schedule(
            expert_id=data["expert"],
            user_id=data["user"],
            time=data["datetime"],
            duration=data.get("duration", 30),
            type=data.get("type", "User")
        )

        document = schedule.to_document()
        schedules_collection.insert_one(document)
        response = ScheduleService.schedule_call_job(document, schedule)
        return jsonify({"message": f"Data received successfully {response}"})

    @staticmethod
    def schedule_call_job(document, schedule: Schedule):
        time = datetime.strptime(schedule.time, "%Y-%m-%dT%H:%M:%S.%fZ")
        record = schedules_collection.find_one(document, {"_id": 1})
        record_id = str(record["_id"]) if record else ""

        response = sm.scheduleCall(
            time, schedule.expert_id, schedule.user_id, record_id)

        return response

    @staticmethod
    def get_slots():
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400

        slot = Slot(
            expert_id=data["expert"],
            utc_date=data["datetime"],
            duration=int(data["duration"])
        )

        output_slots = slot.to_output_slots()
        return jsonify(output_slots)

    @staticmethod
    def get_dynamo_schedules():
        query = """
            query MyQuery($limit: Int = 500) {
                listScheduledJobs(limit: $limit) {
                    nextToken
                    items {
                        id
                        status
                        isDeleted
                        requestMeta
                        scheduledJobTime
                        scheduledJobStatus
                    }
                }
            }
        """

        params = {"limit": 500}
        response = call_graphql(
            query=query, params=params, message="get_scheduled_jobs")

        response = fm.format_schedules(response)

        return jsonify(response)
    
    @staticmethod
    def delete_schedule(scheduleId):
        sm.cancelCall(scheduleId)
        return jsonify({"message": "Schedule deleted successfully"})
