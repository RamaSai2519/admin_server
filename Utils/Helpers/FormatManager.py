from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.config import callsmeta_collection, callsmeta_cache


class FormatManager:
    @staticmethod
    def format_call(call):
        user_id = call["user"] if "user" in call else None
        expert_id = call["expert"] if "expert" in call else None
        call["_id"] = str(call["_id"]) if "_id" in call else None
        call["userName"] = hf.get_user_name(user_id)
        call["user"] = str(user_id)
        call["expertName"] = hf.get_expert_name(expert_id)
        call["expert"] = str(expert_id)
        call["lastModifiedBy"] = (
            str(call["lastModifiedBy"]) if "lastModifiedBy" in call else None
        )
        if call["callId"] in callsmeta_cache:
            callmeta = callsmeta_cache[call["callId"]]
        else:
            callmeta = callsmeta_collection.find_one(
                {"callId": call["callId"]}, {"Conversation Score": 1, "_id": 0}
            )
            callsmeta_cache[call["callId"]] = callmeta
        call["ConversationScore"] = (callmeta["Conversation Score"]) if callmeta else 0
        if "failedReason" in call:
            if call["failedReason"] == "call missed":
                call["status"] = "missed"
            if call["status"] == "successfull":
                call["status"] = "successful"
        return call

    @staticmethod
    def get_formatted_expert(expert):
        expert_id = str(expert["_id"])
        formatted_expert = {
            "_id": expert_id,
            "name": expert["name"] if "name" in expert else None,
            "phoneNumber": expert["phoneNumber"] if "phoneNumber" in expert else None,
            "score": expert["score"] if "score" in expert else 0,
            "status": expert["status"] if "status" in expert else None,
            "createdDate": expert["createdDate"] if "createdDate" in expert else None,
            "repeatRate": expert["repeat_score"] if "repeat_score" in expert else 0,
            "callsShare": expert["calls_share"] if "calls_share" in expert else 0,
            "totalScore": expert["total_score"] if "total_score" in expert else 0,
            "isBusy": expert["isBusy"] if "isBusy" in expert else False,
            "lastModifiedBy": (
                str(expert["lastModifiedBy"]) if "lastModifiedBy" in expert else None
            ),
        }
        return formatted_expert
