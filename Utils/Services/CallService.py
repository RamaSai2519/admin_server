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
            expertId = data["expertId"]
            calls = list(calls_collection.find({"expert": ObjectId(expertId)}))
            isValid = cm.checkValidity(calls[-1])
            if isValid == True:
                userId = calls[-1]["user"]
                user = users_collection.find_one({"_id": ObjectId(userId)})
                response = cm.callUser(expertId, user)
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
            pprint(data)
            expertId = data["expert"]
            userId = data["user"]
            user = users_collection.find_one({"_id": ObjectId(userId)})
            response = cm.callUser(expertId, user)
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
            callmeta = callsmeta_collection.find_one(
                {"callId": id}, {"_id": 0})
            if callmeta:
                formatted_call["Topics"] = callmeta["Topics"]
                formatted_call["Summary"] = callmeta["Summary"]
                formatted_call["User Callback"] = callmeta["User Callback"]
                formatted_call["Score Breakup"] = callmeta["Score Breakup"]
                formatted_call["transcript_url"] = callmeta["transcript_url"]
                formatted_call["Saarthi Feedback"] = callmeta["Saarthi Feedback"]
            return jsonify(formatted_call)
        elif (request.method) == "PUT":
            data = request.get_json()
            new_conversation_score = data["ConversationScore"]
            admin_id = am.get_identity()
            result = calls_collection.update_one(
                {"callId": id},
                {
                    "$set": {
                        "Conversation Score": float(new_conversation_score),
                        "lastModifiedBy": ObjectId(admin_id),
                    }
                },
            )
            if result.modified_count == 0:
                return jsonify({"error": "Failed to update Conversation Score"}), 400
            else:
                return jsonify(new_conversation_score), 200
