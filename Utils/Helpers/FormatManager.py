from Utils.Helpers.HelperFunctions import HelperFunctions as hf

class FormatManager:
    @staticmethod
    def format_call(call):
        user_id = call["user"]
        expert_id = call["expert"]
        call["_id"] = str(call["_id"]) if "_id" in call else None
        call["userName"] = hf.get_user_name(user_id)
        call["user"] = str(user_id)
        call["expertName"] = hf.get_expert_name(expert_id)
        call["expert"] = str(expert_id)
        call["ConversationScore"] = call.pop("Conversation Score", 0)
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
        }
        return formatted_expert
