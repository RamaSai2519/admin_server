from Utils.config import (
    logs_collection,
    applications_collection,
    experts_collection,
    users_collection,
    categories_collection,
    schedules_collection,
)
from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.ScheduleManager import ScheduleManager as sm
from Utils.Helpers.FormatManager import FormatManager as fm
from Utils.Helpers.AuthManager import AuthManager as am
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
        return uf.get_calls()

    @staticmethod
    def get_experts():
        experts = list(experts_collection.find({}, {"categories": 0}))
        formatted_experts = [fm.get_formatted_expert(expert) for expert in experts]
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
            user["lastModifiedBy"] = (
                str(user["lastModifiedBy"]) if "lastModifiedBy" in user else ""
            )
            user["createdDate"] = user["createdDate"].strftime("%Y-%m-%d")
            user["userGameStats"] = (
                str(user["userGameStats"]) if "userGameStats" in user else ""
            )
        return jsonify(users)

    @staticmethod
    def get_categories():
        if request.method == "GET":
            categories = list(categories_collection.find({}, {"_id": 0, "name": 1}))
            category_names = [category["name"] for category in categories]
            return jsonify(category_names)
        elif request.method == "POST":
            data = request.json
            category = data["name"]
            createdDate = datetime.now()
            categories_collection.insert_one(
                {"name": category, "createdDate": createdDate, "active": True}
            )
            return jsonify({"message": "Category added successfully"})

    @staticmethod
    def schedules():
        if request.method == "GET":
            schedules = list(schedules_collection.find()).sort("datetime", 1)
            for schedule in schedules:
                schedule["_id"] = str(schedule["_id"])
                schedule["expert"] = hf.get_expert_name(schedule["expert"])
                schedule["user"] = hf.get_user_name(schedule["user"])
                schedule["lastModifiedBy"] = (
                    str(schedule["lastModifiedBy"])
                    if "lastModifiedBy" in schedule
                    else ""
                )
            return jsonify(schedules)
        elif request.method == "POST":
            data = request.json
            expert_id = data["expert"]
            user_id = data["user"]
            admin_id = am.get_identity()
            time = data["datetime"]
            ist_offset = timedelta(hours=5, minutes=30)
            date_object = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
            ist_time = date_object + ist_offset

            document = {
                "expert": ObjectId(expert_id),
                "user": ObjectId(user_id),
                "lastModifiedBy": ObjectId(admin_id),
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
