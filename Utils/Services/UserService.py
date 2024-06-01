from Utils.config import (
    users_collection,
    deleted_users_collection,
    meta_collection,
    users_cache,
)
from Utils.Helpers.UserManager import UserManager as um
from flask import request, jsonify
from datetime import datetime
from bson import ObjectId


class UserService:
    @staticmethod
    def get_leads():
        final_leads = []
        leads = list(users_collection.find({}, {"Customer Persona": 0}))
        for lead in leads:
            if lead["profileCompleted"] is False:
                lead["_id"] = str(lead["_id"])
                lead["createdDate"] = lead["createdDate"]
                final_leads.append(lead)
        return jsonify(final_leads)

    @staticmethod
    def handle_user(id):
        if request.method == "GET":
            user = users_collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
            meta_doc = meta_collection.find_one({"user": ObjectId(id)})
            if meta_doc:
                user["context"] = str(meta_doc["context"]).split("\n")
                user["source"] = meta_doc["source"]
            return (
                (jsonify(user), 200)
                if user
                else (jsonify({"error": "User not found"}), 404)
            )
        elif request.method == "PUT":
            user_data = request.json
            fields = [
                "name",
                "phoneNumber",
                "city",
                "birthDate",
                "numberOfCalls",
                "context",
                "source",
            ]
            if not any(user_data.get(field) for field in fields):
                return (
                    jsonify({"error": "At least one field is required for update"}),
                    400,
                )
            update_query = {}
            for field in fields:
                value = user_data.get(field)
                if value:
                    if field == "birthDate":
                        value = datetime.strptime(value, "%Y-%m-%d")
                    elif field == "numberOfCalls":
                        value = int(value)
                    elif field == "context":
                        value = "\n".join(value)
                        meta_collection.update_one(
                            {"user": ObjectId(id)}, {"$set": {"context": value}}
                        )
                    update_query[field] = value

            result = users_collection.update_one(
                {"_id": ObjectId(id)}, {"$set": update_query}
            )
            if result.modified_count == 0:
                return jsonify({"error": "User not found"}), 404
            updated_user = users_collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
            users_cache[ObjectId(id)] = updated_user["name"]
            um.updateProfile_status(updated_user)
            return jsonify(updated_user)
        elif request.method == "DELETE":
            user = users_collection.find_one({"_id": ObjectId(id)})
            deleted_users_collection.insert_one(user)
            result = users_collection.delete_one({"_id": ObjectId(id)})
            return (
                (jsonify({"message": "User deleted successfully"}), 200)
                if result.deleted_count
                else (jsonify({"error": "User not found"}), 404)
            )
        else:
            return jsonify({"error": "Invalid request method"}), 404
