from Utils.config import (
    logs_collection,
    applications_collection,
    experts_collection,
    users_collection,
    categories_collection,
    schedules_collection,
)
from Utils.Helpers.ScheduleManager import ScheduleManager as sm
from Utils.Helpers.ExpertManager import ExpertManager as em
from Utils.Helpers.CallManager import CallManager as cm
from datetime import datetime, timedelta
from flask import jsonify, request
from bson import ObjectId


class DataService:
    @staticmethod
    def get_error_logs():
        error_logs = list(logs_collection.find())
        for log in error_logs:
            log["_id"] = str(log["_id"])
        return jsonify(error_logs)

    @staticmethod
    def get_applications():
        applications = list(applications_collection.find())
        for application in applications:
            application["_id"] = str(application["_id"])
        return jsonify(applications)

    @staticmethod
    def get_all_calls():
        return cm.get_calls()

    @staticmethod
    def get_experts():
        experts = list(experts_collection.find({}, {"categories": 0}))
        formatted_experts = [em.get_formatted_expert(expert) for expert in experts]
        return jsonify(formatted_experts)

    @staticmethod
    def get_users():
        users = list(
            users_collection.find(
                {"role": {"$ne": "admin"}, "name": {"$exists": True}},
                {"Customer Persona": 0},
            )
        )
        for user in users:
            user["_id"] = str(user["_id"])
            user["createdDate"] = user["createdDate"].strftime("%Y-%m-%d")
        return jsonify(users)

    @staticmethod
    def get_categories():
        categories = list(categories_collection.find({}, {"_id": 0, "name": 1}))
        category_names = [category["name"] for category in categories]
        return jsonify(category_names)

    @staticmethod
    def schedules():
        if request.method == "GET":
            schedules = list(schedules_collection.find())
            for schedule in schedules:
                schedule["_id"] = str(schedule["_id"])
                expert_id = schedule["expert"]
                expert_id = experts_collection.find_one({"_id": expert_id}, {"name": 1})
                schedule["expert"] = expert_id["name"] if expert_id else ""
                user_id = schedule["user"]
                user_id = users_collection.find_one({"_id": user_id}, {"name": 1})
                schedule["user"] = user_id["name"] if user_id else ""
                if isinstance(schedule["datetime"], datetime):
                    schedule["datetime"] = schedule["datetime"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
            return jsonify(schedules)
        elif request.method == "POST":
            data = request.json
            expert_id = data["expert"]
            user_id = data["user"]
            time = data["datetime"]
            ist_offset = timedelta(hours=5, minutes=30)
            date_object = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
            ist_time = date_object + ist_offset

            document = {
                "expert": ObjectId(expert_id),
                "user": ObjectId(user_id),
                "datetime": ist_time,
                "status": "pending",
            }
            schedules_collection.insert_one(document)
            time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
            hour = ist_time.hour
            minute = ist_time.minute
            year = ist_time.year
            month = ist_time.month - 1
            day = ist_time.day

            expert_docment = experts_collection.find_one({"_id": ObjectId(expert_id)})
            expert_number = expert_docment["phoneNumber"]

            user = users_collection.find_one({"_id": ObjectId(user_id)})
            user_number = user["phoneNumber"]

            record = schedules_collection.find_one(document, {"_id": 1})
            record = str(record["_id"])
            sm.final_call_job(
                record,
                expert_id,
                user_id,
                expert_number,
                user_number,
                year,
                month,
                day,
                hour,
                minute,
            )
            return jsonify({"message": "Data received successfully"})
        else:
            return jsonify({"error": "Invalid request method"}), 404
