from Utils.config import (
    applications_collection,
    categories_collection,
    errorlogs_collection,
    experts_collection,
    timings_collection,
    users_collection,
    indianLanguages,
    cities_cache
)
from Utils.Helpers.UtilityFunctions import UtilityFunctions
from Utils.Helpers.HelperFunctions import HelperFunctions
from Utils.Helpers.FormatManager import FormatManager
from Utils.Helpers.AuthManager import AuthManager
from flask import jsonify, request
from datetime import datetime
from bson import ObjectId


class DataService:
    def __init__(self):
        self.uf = UtilityFunctions
        self.hf = HelperFunctions
        self.fm = FormatManager

    def get_error_logs(self):
        size, offset, page = self.uf.pagination_helper()
        error_logs = list(errorlogs_collection.find().sort(
            "time", -1).skip(offset).limit(size))
        error_logs = list(
            map(self.hf.convert_objectids_to_strings, error_logs))
        total_error_logs = errorlogs_collection.count_documents({})
        return jsonify({"data": error_logs, "total": total_error_logs})

    def get_applications(self):
        formType = request.args.get('formType', 'sarathi')
        size, offset, page = self.uf.pagination_helper()
        applications = list(applications_collection.find(
            {"formType": formType}).sort("createdDate", -1).skip(offset).limit(size))

        for application in applications:
            application["_id"] = str(application["_id"])
            application["workingHours"] = str(application["workingHours"]).replace(
                "'", "").replace("[", "").replace("]", "") if "workingHours" in application else ""
            if "languages" in application:
                languages = application["languages"]
                final_languages = [indianLanguage["value"]
                                   for language in languages for indianLanguage in indianLanguages if indianLanguage["key"] == language]
                application["languages"] = str(final_languages).replace(
                    "'", "").replace("[", "").replace("]", "")

        total_applications = applications_collection.count_documents(
            {"formType": formType})
        return jsonify({"data": applications, "total": total_applications})

    def get_all_calls(self):
        return self.uf.get_calls()

    def get_experts(self):
        experts = list(experts_collection.find(
            {}, {"categories": 0}).sort("name", 1))
        formatted_experts = [self.fm.get_formatted_expert(
            expert) for expert in experts]
        return jsonify(formatted_experts)

    def get_users(self):
        users = list(users_collection.find(
            {"role": {"$ne": "admin"}}, {"Customer Persona": 0}))
        for user in users:
            user["_id"] = str(user["_id"])
            user["lastModifiedBy"] = str(
                user["lastModifiedBy"]) if "lastModifiedBy" in user else ""
            user["userGameStats"] = str(
                user["userGameStats"]) if "userGameStats" in user else ""
        return jsonify(users)

    def get_categories(self):
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
                {"name": category, "createdDate": createdDate, "active": True, "lastModifiedBy": ObjectId(AuthManager.get_identity())})
            return jsonify({"message": "Category added successfully"})

    def get_timings(self):
        if request.method == "GET":
            expertId = request.args.get("expert")
            timings = list(timings_collection.find(
                {"expert": ObjectId(expertId)}))
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

            fields = ["PrimaryStartTime", "PrimaryEndTime",
                      "SecondaryStartTime", "SecondaryEndTime"]
            if field not in fields:
                return jsonify({"error": "Invalid field"}), 400
            try:
                timing = timings_collection.find_one(
                    {"expert": ObjectId(expertId)})
                admin_id = ObjectId(AuthManager.get_identity())
                if timing:
                    timings_collection.update_one({"expert": ObjectId(expertId)}, {
                                                  "$set": {field: value, "lastModifiedBy": admin_id}})
                    return jsonify({"message": "Timing updated successfully"})
                else:
                    timings_collection.insert_one(
                        {"expert": ObjectId(expertId), field: value, "lastModifiedBy": admin_id})
                    return jsonify({"message": "Timing added successfully"})
            except Exception as e:
                print(e)
                return jsonify({"error": str(e)}), 400

    def get_cities(self):
        cities = list(users_collection.distinct("city"))
        for city in cities:
            if city not in cities_cache:
                cities_cache.append({"_id": str(ObjectId()), "city": city})
        return jsonify({"data": cities_cache})
