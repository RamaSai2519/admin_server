from Utils.config import calls_collection, users_collection, admins_collection
from Utils.Helpers.FormatManager import FormatManager as fm
from datetime import datetime, timedelta
import jwt


class UtilityFunctions:
    @staticmethod
    def authenticate(username, password):
        user = admins_collection.find_one({"email": username, "password": password})
        return user

    @staticmethod
    def get_calls(query={}, projection={}):
        admin_ids = [
            user["_id"] for user in users_collection.find({"role": "admin"}, {"_id": 1})
        ]
        calls = list(
            calls_collection.find(
                {
                    "user": {"$nin": admin_ids},
                    **query,
                },
                {
                    "_id": 0,
                    "recording_url": 0,
                    "Score Breakup": 0,
                    "Saarthi Feedback": 0,
                    "User Callback": 0,
                    "Summary": 0,
                    "tonality": 0,
                    "timeSplit": 0,
                    "Sentiment": 0,
                    "Topics": 0,
                    "timeSpent": 0,
                    "userSentiment": 0,
                    "probability": 0,
                    "openingGreeting": 0,
                    "transcript_url": 0,
                    "flow": 0,
                    "closingGreeting": 0,
                    **projection,
                },
            ).sort([("initiatedTime", 1)])
        )

        calls = [fm.format_call(call) for call in calls]
        return calls

    @staticmethod
    def generate_token(name, user_id, phone_number):
        payload = {
            "name": name,
            "userId": user_id,
            "phoneNumber": phone_number,
            "exp": datetime.now() + timedelta(seconds=24 * 60 * 60),
        }
        secret_key = "saltDemaze"
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return token
