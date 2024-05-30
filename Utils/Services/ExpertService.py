from Utils.config import (
    experts_collection,
    categories_collection,
    deleted_experts_collection,
    experts_cache
)
from Utils.Helpers.ExpertManager import ExpertManager as em
from Utils.Helpers.UserManager import UserManager as um
from Utils.Helpers.CallManager import CallManager as cm
from flask import jsonify, request
from bson import ObjectId


class ExpertService:
    @staticmethod
    def get_popup_data(expertId):
        latest_call = cm.get_latest_call(expertId)
        user_id = latest_call["user"]
        userContext = um.get_user_context(ObjectId(user_id))
        remarks = em.get_expert_remarks(ObjectId(expertId))
        repeation = um.determine_user_repeation(ObjectId(user_id), ObjectId(expertId))
        return jsonify(
            {"userContext": userContext, "remarks": remarks, "repeation": repeation}
        )

    @staticmethod
    def handle_expert(id):
        if request.method == "GET":
            expert = experts_collection.find_one({"_id": ObjectId(id)})
            if not expert:
                return jsonify({"error": "Expert not found"}), 404
            expert["_id"] = str(expert["_id"])
            category_names = [
                categories_collection.find_one({"_id": ObjectId(category_id)}).get(
                    "name", ""
                )
                for category_id in expert["categories"]
            ]
            expert["categories"] = category_names
            return jsonify(expert)
        elif request.method == "PUT":
            expert_data = request.json
            required_fields = [
                "name",
                "phoneNumber",
                "topics",
                "description",
                "profile",
                "status",
                "languages",
                "score",
                "calls_share",
                "repeat_score",
                "total_score",
                "categories",
                "openingGreeting",
                "flow",
                "tonality",
                "timeSplit",
                "timeSpent",
                "userSentiment",
                "probability",
                "closingGreeting",
            ]
            if not any(expert_data.get(field) for field in required_fields):
                return (
                    jsonify({"error": "At least one field is required for update"}),
                    400,
                )
            update_query = {}
            for field in required_fields:
                if field == "categories":
                    new_categories_object_ids = [
                        categories_collection.find_one({"name": category_name})["_id"]
                        for category_name in expert_data.get(field, [])
                    ]
                    update_query[field] = new_categories_object_ids
                elif field in expert_data:
                    update_query[field] = (
                        float(expert_data[field])
                        if field in ["calls_share", "score"]
                        else (
                            int(expert_data[field])
                            if field in ["repeat_score", "total_score"]
                            else expert_data[field]
                        )
                    )
            result = experts_collection.update_one(
                {"_id": ObjectId(id)}, {"$set": update_query}
            )
            if result.modified_count == 0:
                return jsonify({"error": "Expert not found"}), 404
            updated_expert = experts_collection.find_one(
                {"_id": ObjectId(id)}, {"_id": 0}
            )
            updated_expert["categories"] = [
                categories_collection.find_one({"_id": ObjectId(category_id)}).get(
                    "name", ""
                )
                for category_id in updated_expert["categories"]
            ]
            experts_cache[ObjectId(id)] = updated_expert["name"]
            return jsonify(updated_expert)
        elif request.method == "DELETE":
            try:
                expert = experts_collection.find_one({"_id": ObjectId(id)})
                deleted_experts_collection.insert_one(expert)
                result = experts_collection.delete_one({"_id": ObjectId(id)})
                if result.deleted_count == 0:
                    return jsonify({"error": "Expert not found"}), 404
                return jsonify({"message": "Expert deleted successfully"})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            return jsonify({"error": "Invalid request method"}), 404
