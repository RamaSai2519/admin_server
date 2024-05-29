from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.config import statuslogs_collection


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
        login_logs = list(
            statuslogs_collection.find({"expert": expert_id, "status": "online"})
        )
        logged_in_hours = hf.calculate_logged_in_hours(login_logs)
        formatted_expert = {
            "_id": expert_id,
            "name": expert["name"],
            "phoneNumber": expert["phoneNumber"],
            "score": expert["score"],
            "status": expert["status"],
            "createdDate": expert["createdDate"],
            "loggedInHours": logged_in_hours,
            "repeatRate": expert["repeat_score"],
            "callsShare": expert["calls_share"],
            "totalScore": expert["total_score"],
            "isBusy": expert["isBusy"],
        }
        return formatted_expert
