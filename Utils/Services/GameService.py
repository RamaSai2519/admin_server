from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.config import users_collection, experts_collection
from flask import request, jsonify
from bson import ObjectId


class GameService:
    @staticmethod
    def get_profiles():
        userId = request.args.get("userId")
        expertId = request.args.get("expertId")

        user = users_collection.find_one({"_id": ObjectId(userId)})
        userName = hf.get_user_name(ObjectId(userId))

        expert = experts_collection.find_one({"_id": ObjectId(expertId)})
        expertName = hf.get_expert_name(ObjectId(expertId))

        if not user or not expert:
            return jsonify({"message": "Invalid user or expert"}), 400

        response = {
            "userName": userName,
            "expertName": expertName,
            "expertImage": expert["profile"]
        }

        return jsonify(response)
