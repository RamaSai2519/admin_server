from Utils.Helpers.FormatManager import FormatManager as fm
from Utils.Helpers.CallManager import CallManager as cm
from Utils.config import calls_collection
from flask import request, jsonify
from bson import ObjectId


class CallService:
    @staticmethod
    def expert_call_user():
        try:
            data = request.json
            expertId = data["expertId"]
            calls = list(calls_collection.find({"expert": ObjectId(expertId)}))
            isValid = cm.checkValidity(calls[-1])
            if isValid == True:
                userId = calls[-1]["user"]
                response = cm.callUser(expertId, userId)
                if response["data"] == {}:
                    return response["error"]
                else:
                    return "Call Initiated Successfully"
            else:
                return isValid
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @staticmethod
    def connect():
        try:
            data = request.json
            expertId = data["expert"]
            userId = data["user"]
            response = cm.callUser(expertId, userId)
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
            return jsonify(formatted_call)
        elif (request.method) == "PUT":
            data = request.get_json()
            new_conversation_score = data["ConversationScore"]
            result = calls_collection.update_one(
                {"callId": id},
                {"$set": {"Conversation Score": float(new_conversation_score)}},
            )

            if result.modified_count == 0:
                return jsonify({"error": "Failed to update Conversation Score"}), 400
            else:
                return jsonify(new_conversation_score), 200
