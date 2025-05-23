from Utils.config import calls_collection, users_collection, callsmeta_collection
from Utils.Helpers.FormatManager import FormatManager as fm
from Utils.Helpers.AuthManager import AuthManager as am
from Utils.Helpers.CallManager import CallManager as cm
from flask import request, jsonify
from bson import ObjectId
from pprint import pprint


class CallService:
    @staticmethod
    def expert_call_user():
        try:
            data = request.json
            if not data:
                return jsonify({"error": "Missing data"}), 400
            expertId = data["expertId"]
            calls = list(calls_collection.find({"expert": ObjectId(expertId)}))
            isValid = cm.checkValidity(calls[-1])
            if isValid == True:
                userId = calls[-1]["user"]
                user = users_collection.find_one({"_id": ObjectId(userId)})
                response = cm.callUser(expertId, user)
                if not response:
                    return jsonify({"error": "Failed to initiate call"}), 400
                return response
            else:
                return isValid
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def connect():
        try:
            data = request.json
            if not data:
                return jsonify({"error": "Missing data"}), 400
            expertId = data["expert"]
            userId = data["user"]
            user = users_collection.find_one({"_id": ObjectId(userId)})
            response = cm.callUser(expertId, user)
            if not response:
                return jsonify({"message": "Failed to initiate call"}), 400
            return response
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def handle_call(id):
        if (request.method) == "GET":
            call = calls_collection.find_one({"callId": id})
            if not call:
                return jsonify({"error": "Call not found"}), 404
            formatted_call = fm.format_call(call)
            callmeta: dict = callsmeta_collection.find_one(
                {"callId": id}, {"_id": 0})
            if callmeta:
                for key, value in callmeta.items():
                    formatted_call[key] = value
            return jsonify(formatted_call)
        elif (request.method) == "PUT":
            data = request.get_json()
            new_conversation_score = data["ConversationScore"]
            admin_id = am.get_identity()
            result = calls_collection.update_one(
                {"callId": id},
                {
                    "$set": {
                        "conversationScore": float(new_conversation_score),
                        "lastModifiedBy": ObjectId(admin_id),
                    }
                },
            )
            if result.modified_count == 0:
                return jsonify({"error": "Failed to update Conversation Score"}), 400
            else:
                return jsonify(new_conversation_score), 200
