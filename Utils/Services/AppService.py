from Utils.config import (
    deleted_schedules_collection,
    fcm_tokens_collection,
    schedules_collection,
    experts_collection,
    users_collection,
)
from Utils.Helpers.ScheduleManager import ScheduleManager as sm
from Utils.Helpers.InsightsManager import InsightsManager as im
from Utils.Helpers.AuthManager import AuthManager as am
from datetime import datetime, timedelta
from flask import request, jsonify
from bson import ObjectId
import pytz


class AppService:
    @staticmethod
    def get_insights():
        insights = im.get_call_insights()

        # Create the new structure for successfulCalls
        successfulCalls = [
            {
                "key": "1",
                "category": "< 15 mins",
                "value": insights.get("_15min", "0%"),
            },
            {
                "key": "2",
                "category": "15-30 mins",
                "value": insights.get("_15_30min", "0%"),
            },
            {
                "key": "3",
                "category": "30-45 mins",
                "value": insights.get("_30_45min", "0%"),
            },
            {
                "key": "4",
                "category": "45-60 mins",
                "value": insights.get("_45_60min", "0%"),
            },
            {
                "key": "5",
                "category": "> 60 mins",
                "value": insights.get("_60min_", "0%"),
            },
        ]

        # Create the new structure for avgCallDuration
        avgCallDuration = [
            {
                "key": "1",
                "category": "First Call",
                "value": insights.get("one_call", "0"),
            },
            {
                "key": "2",
                "category": "Second Call",
                "value": insights.get("two_calls", "0"),
            },
            {
                "key": "3",
                "category": "Repeat Calls",
                "value": insights.get("repeat_calls", "0"),
            },
            {
                "key": "4",
                "category": "Scheduled Calls",
                "value": insights.get("scheduled_avg_duration", "0"),
            },
            {
                "key": "5",
                "category": "Organic Calls",
                "value": insights.get("organic_avg_duration", "0"),
            },
        ]

        # Create the new structure for otherStats
        otherStats = [
            {
                "key": "1",
                "category": "First Call Split",
                "value": insights.get("first_calls_split", "0%"),
            },
            {
                "key": "2",
                "category": "Second Call Split",
                "value": insights.get("second_calls_split", "0%"),
            },
            {
                "key": "3",
                "category": "Repeat Call Split",
                "value": insights.get("repeat_calls_split", "0%"),
            },
        ]

        # Combine all into a new dictionary
        callInsights = {
            "successfulCalls": successfulCalls,
            "avgCallDuration": avgCallDuration,
            "otherStats": otherStats,
        }

        return jsonify(callInsights)

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
    def update_schedule(id):
        if request.method == "PUT":
            try:
                data = request.json
                expert = data["expert"]
                expert = experts_collection.find_one({"name": expert})
                expert = str(expert["_id"])
                expert_number = expert["phoneNumber"]
                user = data["user"]
                user = users_collection.find_one({"name": user})
                user_number = user["phoneNumber"]
                user = str(user["_id"])
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
            expert = experts_collection.find_one(
                {"_id": expert_id}, {"name": 1})
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
