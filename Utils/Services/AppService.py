from Utils.config import (
    deleted_schedules_collection,
    fcm_tokens_collection,
    schedules_collection,
    experts_collection,
    users_collection,
)
from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from Utils.Helpers.ScheduleManager import ScheduleManager as sm
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.ExpertManager import ExpertManager as em
from Utils.Helpers.AuthManager import AuthManager as am
from Utils.Helpers.CallManager import CallManager as cm
from datetime import datetime, timedelta
from flask import request, jsonify
from bson import ObjectId
import pytz


class AppService:
    @staticmethod
    def save_fcm_token():
        data = request.json
        token = data["token"]
        tokens = list(fcm_tokens_collection.find())
        if token in [t["token"] for t in tokens]:
            return jsonify({"message": "FCM token already saved"}), 200
        elif token:
            fcm_tokens_collection.insert_one({"token": token})
            return jsonify({"message": "FCM token saved successfully"}), 200
        else:
            return jsonify({"error": "FCM token missing"}), 400

    @staticmethod
    def get_dashboard_stats():
        current_date = datetime.now(pytz.timezone("Asia/Kolkata"))
        today_start = datetime.combine(current_date, datetime.min.time())
        today_end = datetime.combine(current_date, datetime.max.time())
        total_calls = len(uf.get_calls())
        today_calls_query = {"initiatedTime": {"$gte": today_start, "$lt": today_end}}
        today_calls = uf.get_calls(today_calls_query, {})
        today_successful_calls = sum(
            1 for call in today_calls if call["status"] == "successful"
        )
        today_total_calls = len(today_calls)
        online_saarthis = em.get_online_saarthis()
        total_successful_calls, total_duration_seconds = (
            cm.get_total_successful_calls_and_duration()
        )
        average_call_duration = (
            hf.format_duration(total_duration_seconds / total_successful_calls)
            if total_successful_calls
            else "0 minutes"
        )
        total_failed_calls = total_calls - total_successful_calls
        today_failed_calls = today_total_calls - today_successful_calls
        stats_data = {
            "totalCalls": total_calls,
            "successfulCalls": total_successful_calls,
            "todayCalls": today_total_calls,
            "failedCalls": total_failed_calls,
            "todayFailedCalls": today_failed_calls,
            "todaySuccessfulCalls": today_successful_calls,
            "averageCallDuration": average_call_duration,
            "onlineSaarthis": online_saarthis,
        }

        return jsonify(stats_data)

    @staticmethod
    def update_schedule(id):
        if request.method == "PUT":
            try:
                data = request.json
                expert = data["expert"]
                expert = experts_collection.find_one({"name": expert})
                expert = str(expert["_id"])
                expert_number = (expert["phoneNumber"])
                user = (data["user"])
                user = users_collection.find_one({"name": user})
                user_number = (user["phoneNumber"])
                user = (str(user["_id"]))
                time = data["datetime"]
                ist_offset = timedelta(hours=5, minutes=30)
                date_object = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
                ist_time = date_object + ist_offset

                sm.cancel_final_call(id)
                admin_id = am.get_identity()
                result = schedules_collection.update_one(
                    {"_id": ObjectId(id)},
                    {
                        "$set": {
                            "lastModifiedBy": ObjectId(admin_id),
                            "expert": ObjectId(expert),
                            "user": ObjectId(user),
                            "datetime": time,
                        }
                    },
                )
                time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
                hour = ist_time.hour - 1
                minute = ist_time.minute
                year = ist_time.year
                month = ist_time.month - 1
                day = ist_time.day

                sm.final_call_job(
                    id, expert_number, user_number, year, month, day, hour, minute
                )

                if result.modified_count == 0:
                    return jsonify({"error": "Failed to update schedule"}), 400

                return jsonify({"message": "Schedule updated successfully"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        elif request.method == "DELETE":
            try:
                sm.cancel_final_call(id)
                schedule = schedules_collection.find_one({"_id": ObjectId(id)})
                deleted_schedules_collection.insert_one(schedule)
                result = schedules_collection.delete_one({"_id": ObjectId(id)})
                if result.deleted_count == 0:
                    return jsonify({"error": "Schedule not found"}), 404
                return jsonify({"message": "Schedule deleted successfully"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        elif request.method == "GET":
            schedule = schedules_collection.find_one({"_id": ObjectId(id)})
            if not schedule:
                return jsonify({"error": "Schedule not found"}), 404
            schedule["_id"] = (str(schedule["_id"]),)
            expert_id = (schedule["expert"],)
            expert = experts_collection.find_one({"_id": expert_id}, {"name": 1})
            schedule["expert"] = expert["name"] if expert else ""
            user_id = schedule["user"]
            user = users_collection.find_one({"_id": user_id}, {"name": 1})
            schedule["user"] = user["name"] if user else ""
            timestamp_utc = datetime.strptime(
                schedule["datetime"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            ist_timezone = pytz.timezone("Asia/Kolkata")
            timestamp_ist = timestamp_utc.astimezone(ist_timezone)
            schedule["datetime"] = timestamp_ist.strftime(r"%Y-%m-%d %H:%M:%S")
            return jsonify(schedule)

    @staticmethod
    def approve_application(id, level):
        data = request.json
        status = data["status"]
        sm.cancel_final_call(id, level)
        result = schedules_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": {"status": status}}
        )
        schedule_record = schedules_collection.find_one({"_id": ObjectId(id)})
        expert_id = schedule_record["expert"]
        expert = experts_collection.find_one({"_id": expert_id})
        expert_number = expert["phoneNumber"]
        user_id = schedule_record["user"]
        user = users_collection.find_one({"_id": user_id})
        user_number = user["phoneNumber"]
        scheduled_Call_time = schedule_record["datetime"]
        scheduled_Call_time = datetime.strptime(
            scheduled_Call_time, "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        sm.final_call_job(
            id,
            expert_number,
            user_number,
            scheduled_Call_time.year,
            scheduled_Call_time.month,
            scheduled_Call_time.day,
            scheduled_Call_time.hour,
            scheduled_Call_time.minute,
        )
        if result.modified_count == 0:
            return jsonify({"error": "Application not found"}), 404
        return jsonify({"message": "Application updated successfully"}), 200
