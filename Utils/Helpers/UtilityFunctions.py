from Utils.config import calls_collection, users_collection
from Utils.Helpers.FormatManager import FormatManager as fm


class UtilityFunctions:
    @staticmethod
    def get_calls(query={}, projection={}, exclusion=True):
        admin_ids = [
            user["_id"] for user in users_collection.find({"role": "admin"}, {"_id": 1})
        ]
        if exclusion:
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
        else:
            calls = list(
                calls_collection.find(
                    {
                        "user": {"$nin": admin_ids},
                        **query,
                    },
                    {
                        **projection,
                    },
                ).sort([("initiatedTime", 1)])
            )

        calls = [fm.format_call(call) for call in calls]
        return calls

    @staticmethod
    def get_calls_count(query={}):
        admin_ids = [
            user["_id"] for user in users_collection.find({"role": "admin"}, {"_id": 1})
        ]
        count = calls_collection.count_documents({"user": {"$nin": admin_ids}, **query})
        return count
