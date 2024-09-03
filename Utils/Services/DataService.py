from Utils.config import (
    club_intersts_collection,
    applications_collection,
    categories_collection,
    errorlogs_collection,
    experts_collection,
    timings_collection,
    users_collection,
    indianLanguages,
    cities_cache,
    db
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
            {"role": {"$ne": "admin"}, "profileCompleted": True}, {"Customer Persona": 0}))
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
            prev_category = categories_collection.find_one({"name": category})
            if prev_category:
                return jsonify({"error": "Category already exists"}), 400
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
                timing["lastModifiedBy"] = str(
                    timing["lastModifiedBy"]) if "lastModifiedBy" in timing else ""
            return jsonify(timings)
        if request.method == "POST":
            data = request.json
            if not data:
                return jsonify({"error": "Invalid request data"}), 400
            print(data)
            expertId = data["expertId"]
            day = data["row"]["key"]
            field = data["row"]["field"]
            value = data["row"]["value"]

            fields = ["PrimaryStartTime", "PrimaryEndTime",
                      "SecondaryStartTime", "SecondaryEndTime"]
            if field not in fields:
                return jsonify({"error": "Invalid field"}), 400
            try:
                admin_id = ObjectId(AuthManager.get_identity())
                filter = {"expert": ObjectId(expertId), "day": day}
                timings_collection.update_one(filter, {
                    "$set": {field: value, "lastModifiedBy": admin_id}})
                return jsonify({"message": "Timing updated successfully"})
            except Exception as e:
                print(e)
                return jsonify({"error": str(e)}), 400

    def get_cities(self):
        cities = list(users_collection.distinct("city"))
        for city in cities:
            if city not in cities_cache:
                cities_cache.append({"_id": city, "city": city})
        return jsonify({"data": cities_cache})

    def get_club_interests(self):
        size, offset, page = self.uf.pagination_helper()
        club_interests = list(club_intersts_collection.find(
            {}).sort("createdDate", -1).skip(offset).limit(size))
        for club_interest in club_interests:
            user = users_collection.find_one(
                {"_id": ObjectId(club_interest["userId"])},
                {"_id": 0, "name": 1, "phoneNumber": 1})
            if user:
                club_interest["name"] = user["name"]
                club_interest["phoneNumber"] = user["phoneNumber"]
            else:
                club_intersts_collection.delete_one(
                    {"_id": club_interest["_id"]})
        total_docs = club_intersts_collection.count_documents({})
        club_interests = list(
            map(self.hf.convert_objectids_to_strings, club_interests))
        return jsonify({"data": club_interests, "total": total_docs})

    def generate_filter_options(self):
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400

        collection = data["collection"]
        field = data["field"]
        collection = db[collection]
        filter_options = list(collection.distinct(field))
        filter_options = [{"text": value, "value": value}
                          for value in filter_options]
        return jsonify(filter_options)

    def get_filtered_data(self):
        data = dict(request.json)
        if not data:
            return jsonify({"error": "Invalid request data"}), 400

        page = data.get("page", 1)
        size = data.get("size", 10)
        filters: dict = data.get("filter", {})
        collection_name = data.get("collection")
        if not collection_name:
            return jsonify({"error": "Collection name is required"}), 400

        mongo_collection = db[collection_name]
        query = {}
        for key, value in filters.items():
            if value is not None:
                obIds = users_collection.find({"name": {"$in": value}}, {"_id": 1}) if key == "user" else experts_collection.find(
                    {"name": {"$in": value}}, {"_id": 1}) if key == "expert" else None
                query[key] = {"$in": [obId["_id"]
                                      for obId in obIds]} if obIds else {"$in": value}
        total = mongo_collection.count_documents(query)
        output_data = list(mongo_collection.find(query).skip(
            (page - 1) * size).limit(size))

        if collection_name == "schedules":
            output_data = self.uf.format_schedules(output_data)
        final_data = list(
            map(self.hf.convert_objectids_to_strings, output_data))

        return jsonify({
            "page": page,
            "size": size,
            "data": final_data,
            "total": total
        })
