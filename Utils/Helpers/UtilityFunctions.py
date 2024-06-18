from Utils.config import calls_collection, users_collection, experts_collection
from Utils.Helpers.FormatManager import FormatManager as fm


class UtilityFunctions:
    @staticmethod
    def get_calls(query={}, projection={}, exclusion=True, format=True):
        admin_ids = [
            user["_id"] for user in users_collection.find({"role": "admin"}, {"_id": 1})
        ]
        test_expert_id = experts_collection.find_one(
            {"name": "Test"}, {"_id": 1}
        )["_id"]
        exclusion_projection = {
            "callId": 1,
            "user": 1,
            "expert": 1,
            "status": 1,
            "initiatedTime": 1,
            "duration": 1,
            "lastModifiedBy": 1,
            "failedReason": 1,
            "Conversation Score": 1,
        }
        if exclusion:
            projection = {**exclusion_projection, **projection}
        calls = list(
            calls_collection.find(
                {"user": {"$nin": admin_ids}, "expert": {
                    "$ne": test_expert_id}, **query}, projection
            ).sort("initiatedTime", 1)
        )
        if format:
            calls = [fm.format_call(call) for call in calls]
        return calls

    @staticmethod
    def get_calls_count(query={}):
        admin_ids = [
            user["_id"] for user in users_collection.find({"role": "admin"}, {"_id": 1})
        ]
        count = calls_collection.count_documents(
            {"user": {"$nin": admin_ids}, **query})
        return count
