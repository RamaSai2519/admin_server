from flask import request, jsonify
from datetime import datetime
from bson import ObjectId
from Utils.Helpers.EngagementHelper import EngagementHelper
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from Utils.config import meta_collection, users_collection, calls_collection
from pprint import pprint


class EngagementService:
    def __init__(self):
        self.meta_fields = ["remarks", "expert", "lastReached",
                            "status", "userStatus", "source"]

    def get_engagement_data(self):
        try:
            if request.method == "GET":
                return self.handle_get_request()
            elif request.method == "POST":
                return self.handle_post_request()
            else:
                return self.response_error("Invalid request method", 405)
        except Exception as e:
            print(e)
            return self.response_error(str(e), 500)

    def handle_get_request(self):
        size, offset, page = uf.pagination_helper()
        time = datetime.now()

        user_data = self.get_user_data(size, offset, time)
        total_users = users_collection.count_documents(
            {"role": {"$ne": "admin"}})

        return jsonify({
            "data": user_data, "total": total_users,
            "page": page, "pageSize": size
        })

    def handle_post_request(self):
        data = request.json
        if not data:
            return self.response_error("Missing data", 400)

        user_id = data["key"]
        user_field = data["field"]
        user_value = data["value"]

        if not user_id or not user_field or user_value is None:
            return self.response_error("Invalid input data", 400)

        if not self.is_valid_user(user_id):
            return self.response_error("User not found", 404)

        engagement_helper = EngagementHelper(user_id=user_id)
        try:
            if user_field in self.meta_fields:
                return engagement_helper.update_meta_data(user_field, user_value)
            else:
                return engagement_helper.update_user_data(user_field, user_value)
        except Exception as e:
            return self.response_error(str(e), 500)

    def get_user_data(self, size, offset, time):
        users = users_collection.find(
            {"role": {"$ne": "admin"}},
            {"Customer Persona": 0, "lastModifiedBy": 0, "userGameStats": 0}
        ).sort("createdDate", -1).skip(offset).limit(size)

        user_data = []
        for user in users:
            user["_id"] = str(user["_id"])
            user["slDays"] = (time - user["createdDate"]).days
            if "profileCompleted" in user and user["profileCompleted"] is False:
                user["type"] = "Lead"
            else:
                user["type"] = "User"

            self.populate_meta_data(user)
            self.populate_call_data(user, time)

            user_data.append(user)
        return user_data

    def populate_call_data(self, user, time):
        last_call = calls_collection.find_one(
            {"user": ObjectId(user["_id"]),
             "status": "successfull", "failedReason": ""},
            {"_id": 0, "initiatedTime": 1, "expert": 1},
            sort=[("initiatedTime", -1)]
        )

        if last_call:
            user["lastCallDate"] = last_call["initiatedTime"]
            user["callAge"] = (time - last_call["initiatedTime"]).days
            if not user["expert"] or user["expert"] == "":
                user["expert"] = hf.get_expert_name(last_call["expert"])
        else:
            user["lastCallDate"] = "No Calls"
            user["callAge"] = 0

        user["callsDone"] = calls_collection.count_documents(
            {"user": ObjectId(user["_id"]),
             "status": "successfull", "failedReason": ""}
        )
        user["callStatus"] = uf.get_call_status(user["callsDone"])

    def populate_meta_data(self, user):
        user_meta = meta_collection.find_one({"user": ObjectId(user["_id"])})
        for field in self.meta_fields:
            if user_meta:
                user[field] = user_meta[field] if field in user_meta else ""
            else:
                user[field] = ""

    def is_valid_user(self, user_id):
        return users_collection.find_one({"_id": ObjectId(user_id)}) is not None

    def response_error(self, message, status_code):
        return jsonify({"error": message}), status_code
