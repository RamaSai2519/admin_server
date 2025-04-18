from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.config import expertlogs_collection
from bson import ObjectId
import json


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
        if "failedReason" in call:
            if call["failedReason"] == "call missed":
                call["status"] = "missed"
            if call["status"] == "successful":
                call["status"] = "successful"
        return call

    @staticmethod
    def get_formatted_expert(expert):
        expert_id = str(expert["_id"])
        total_timeSpent = expertlogs_collection.find(
            {"expert": ObjectId(expert_id), "duration": {
                "$exists": True}}, {"duration": 1}
        )
        total_timeSpent = sum(
            [
                log["duration"]
                for log in total_timeSpent
            ]
        )
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
                str(expert["lastModifiedBy"]
                    ) if "lastModifiedBy" in expert else None
            ),
            "timeSpent": round((total_timeSpent / 3600), 2) if total_timeSpent else 0,
        }
        return formatted_expert

    @staticmethod
    def format_schedules(schedules):
        for schedule in schedules:
            schedule["requestMeta"] = json.loads(schedule["requestMeta"])
            schedule["expert"] = hf.get_expert_name(
                ObjectId(schedule["requestMeta"]["expertId"]))
            schedule["user"] = hf.get_user_name(
                ObjectId(schedule["requestMeta"]["userId"]))
            schedule["datetime"] = schedule["scheduledJobTime"]
        return {"data": schedules}
