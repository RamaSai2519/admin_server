from Utils.config import calls_collection, users_collection, experts_collection
from Utils.Helpers.FormatManager import FormatManager as fm
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from flask import request


class UtilityFunctions:
    """
    A utility class containing static methods for retrieving calls data and pagination assistance.
    - `get_calls(query={}, projection={}, exclusion=True, format=True)`: Retrieves calls based on the query parameters and exclusion criteria.
    - `get_calls_count(query={})`: Retrieves the count of calls based on the query parameters.
    - `pagination_helper()`: Helps with pagination by extracting page and size parameters from the request and calculating the offset.
    """
    @staticmethod
    def get_calls(query={}, projection={}, exclusion=True, format=True):
        admin_ids = [
            user["_id"] for user in users_collection.find({"role": "admin"}, {"_id": 1})
        ]
        test_expert = experts_collection.find_one(
            {"name": "Test"}, {"_id": 1}
        )
        test_expert_id = test_expert["_id"] if test_expert else None
        exclusion_projection = {
            "callId": 1,
            "user": 1,
            "expert": 1,
            "status": 1,
            "initiatedTime": 1,
            "duration": 1,
            "lastModifiedBy": 1,
            "failedReason": 1,
            "conversationScore": 1,
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

    @staticmethod
    def pagination_helper():
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        offset = (page - 1) * size

        return size, offset, page

    @staticmethod
    def get_call_status(calls_done):
        if calls_done == 0:
            return "First call Pending"
        elif calls_done == 1:
            return "First call Done"
        elif calls_done == 2:
            return "Second call Done"
        elif calls_done == 3:
            return "Third call Done"
        else:
            return "Engaged"

    @staticmethod
    def format_schedules(schedules):
        for schedule in schedules:
            schedule["_id"] = str(schedule["_id"])
            schedule["expert"] = hf.get_expert_name(schedule["expert"])
            schedule["user"] = hf.get_user_name(schedule["user"])
            schedule["callStatus"] = schedule["callStatus"] if "callStatus" in schedule else ""
        return schedules
