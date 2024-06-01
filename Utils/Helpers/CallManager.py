from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from Utils.config import calls_collection
from datetime import datetime, timedelta
from pymongo import DESCENDING
from bson import ObjectId
import requests
import pytz
import json


class CallManager:
    @staticmethod
    def get_total_successful_calls_and_duration():
        successful_calls_data = uf.get_calls(
            {"status": "successfull", "duration": {"$exists": True}}
        )
        total_seconds = [
            hf.get_total_duration_in_seconds(call.get("duration", "00:00:00"))
            for call in successful_calls_data
            if hf.get_total_duration_in_seconds(call.get("duration", "00:00:00")) > 60
        ]
        return len(total_seconds), sum(total_seconds)

    @staticmethod
    def callUser(expertId, user):
        url = "http://api.sukoon.love/api/call/make-call"
        token = uf.generate_token(user["name"], str(user["_id"]), user["phoneNumber"])
        payload = json.dumps(
            {
                "expertId": expertId,
            }
        )
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json()

    @staticmethod
    def checkValidity(call):
        initiated_time = call["initiatedTime"]
        if isinstance(initiated_time, str):
            initiated_time = datetime.strptime(initiated_time, "%Y-%m-%d %H:%M:%S.%f")

        utc_zone = pytz.utc
        ist_zone = pytz.timezone("Asia/Kolkata")
        initiated_time = initiated_time.replace(tzinfo=utc_zone).astimezone(ist_zone)
        current_time = datetime.now(ist_zone)

        try:
            if call["duration"] != "":
                duration = hf.get_total_duration_in_seconds(call["duration"])
                duration_timedelta = timedelta(seconds=duration)
                end_time = initiated_time + duration_timedelta
                time_difference = current_time - end_time
            else:
                time_difference = current_time - initiated_time

            if time_difference.total_seconds() <= 600:
                return True
            else:
                hours, remainder = divmod(time_difference.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                return f"The call is {int(hours)} hours and {int(minutes)} minutes old and can't be reconnected."
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def get_latest_call(expertId):
        expertId = ObjectId(expertId)
        call = calls_collection.find_one(
            {"$or": [{"_id": expertId}, {"expert": expertId}, {"user": expertId}]},
            sort=[("initiatedTime", DESCENDING)],
        )
        return call
