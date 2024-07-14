from Utils.config import (
    userwebhookmessages_collection,
    applications_collection,
    wafeedback_collection,
    categories_collection,
    errorlogs_collection,
    schedules_collection,
    experts_collection,
    timings_collection,
    users_collection,
    indianLanguages
)
from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.ScheduleManager import ScheduleManager as sm
from Utils.Helpers.FormatManager import FormatManager as fm
from Utils.Helpers.AuthManager import AuthManager as am
from datetime import datetime, timedelta
from flask import jsonify, request
from bson import ObjectId
import pytz


class DataService:
    """
    A class that provides static methods to retrieve data.
    - get_error_logs(): Retrieves error logs from a collection, converts the '_id' field to a string, and returns the logs as JSON.
    - get_applications(): Processes feedback data by getting the expert name, modifying the body text, and returns the feedbacks data along with total count, page, and page size as JSON.
    - get_all_calls(): Retrieves all calls data from a collection and returns the calls data as JSON.
    - get_experts(): Retrieves experts data from a collection, formats the data, and returns the experts data as JSON.
    - get_users(): Retrieves users data from a collection, modifies the '_id', 'lastModifiedBy', 'createdDate', and 'userGameStats' fields, and returns the users data as JSON.
    - get_categories(): Retrieves categories data from a collection, extracts the 'name' field, and returns the category names as JSON.
    - get_timings(): Retrieves timings data from a collection, processes the data, and returns the timings data as JSON.
    """
    @staticmethod
    def get_error_logs():
        size, offset, page = uf.pagination_helper()
        error_logs = list(errorlogs_collection.find().sort(
            "time", -1).skip(offset).limit(size))
        for error_log in error_logs:
            error_log["_id"] = str(error_log["_id"])
        total_error_logs = errorlogs_collection.count_documents({})
        return jsonify({"data": error_logs, "total": total_error_logs})

    @staticmethod
    def get_applications():
        formType = request.args.get('formType', 'sarathi')
        size, offset, page = uf.pagination_helper()
        applications = list(applications_collection.find(
            {"formType": formType}
        ).sort("createdAt", -1).skip(offset).limit(size))

        for application in applications:
            application["_id"] = str(application["_id"])
            application["workingHours"] = str(application["workingHours"]).replace(
                "'", "").replace("[", "").replace("]", "") if "workingHours" in application else ""
            if "languages" in application:
                languages = application["languages"]
                final_languages = []
                for language in languages:
                    for indianLanguage in indianLanguages:
                        if indianLanguage["key"] == language:
                            language = indianLanguage["value"]
                            final_languages.append(language)
                application["languages"] = str(final_languages).replace(
                    "'", "").replace("[", "").replace("]", "")
        total_applications = applications_collection.count_documents(
            {"formType": formType})
        return jsonify({
            "data": applications,
            "total": total_applications
        })

    @staticmethod
    def get_all_calls():
        return uf.get_calls()

    @staticmethod
    def get_experts():
        experts = list(experts_collection.find(
            {}, {"categories": 0}).sort("name", 1))
        formatted_experts = [fm.get_formatted_expert(
            expert) for expert in experts]
        return jsonify(formatted_experts)

    @staticmethod
    def get_users():
        users = list(
            users_collection.find(
                {"role": {"$ne": "admin"}, "profileCompleted": True,
                    "city": {"$exists": True}},
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
            categories = list(categories_collection.find(
                {}, {"_id": 0, "name": 1}))
            category_names = [category["name"] for category in categories]
            return jsonify(category_names)
        elif request.method == "POST":
            data = request.json
            if not data:
                return jsonify({"error": "Invalid request data"}), 400
            category = data["name"]
            createdDate = datetime.now()
            categories_collection.insert_one(
                {"name": category, "createdDate": createdDate, "active": True}
            )
            return jsonify({"message": "Category added successfully"})

    @staticmethod
    def get_timings():
        if request.method == "GET":
            expertId = request.args.get("expert")
            timings = list(timings_collection.find({
                "expert": ObjectId(expertId)
            }))
            for timing in timings:
                timing["_id"] = str(timing["_id"])
                timing["expert"] = str(timing["expert"])
            return jsonify(timings)
        if request.method == "POST":
            data = request.json
            if not data:
                return jsonify({"error": "Invalid request data"}), 400
            expertId = data["expertId"]
            field = data["row"]["field"]
            value = data["row"]["value"]

            fields = [
                "PrimaryStartTime",
                "PrimaryEndTime",
                "SecondaryStartTime",
                "SecondaryEndTime",
            ]
            if field not in fields:
                return jsonify({"error": "Invalid field"}), 400
            try:
                timing = timings_collection.find_one({
                    "expert": ObjectId(expertId)
                })

                if timing:
                    timings_collection.update_one({"expert": ObjectId(expertId)}, {
                                                  "$set": {field: value}})
                    return jsonify({"message": "Timing updated successfully"})
                else:
                    timings_collection.insert_one(
                        {"expert": ObjectId(expertId), field: value})
                    return jsonify({"message": "Timing added successfully"})
            except Exception as e:
                print(e)
                return jsonify({"error": str(e)}), 400
