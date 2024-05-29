from Utils.config import experts_collection, meta_collection, experts_cache
from Utils.Helpers.FormatManager import FormatManager as fm
from datetime import datetime


class ExpertManager:
    @staticmethod
    def calculate_logged_in_hours(login_logs):
        total_logged_in_hours = 0
        last_logged_out_time = None

        for log in login_logs:
            if log["status"] == "online":
                logged_in_at = log["date"]
                logged_out_at = (
                    datetime.now()
                    if last_logged_out_time is None
                    else last_logged_out_time
                )
            else:
                logged_out_at = log["date"]
                logged_in_at = last_logged_out_time
            if logged_in_at is not None and logged_out_at is not None:
                total_logged_in_hours += (
                    logged_out_at - logged_in_at
                ).total_seconds() / 3600
            last_logged_out_time = logged_out_at

        return total_logged_in_hours

    @staticmethod
    def get_online_saarthis():
        online_saarthis = experts_collection.find(
            {"status": {"$regex": "online"}}, {"categories": 0}
        )
        return [fm.get_formatted_expert(expert) for expert in online_saarthis]

    @staticmethod
    def get_expert_remarks(id):
        try:
            documents = list(meta_collection.find({"expert": id}))
            if len(documents) > 0:
                remarks = []
                for document in documents:
                    if "remark" in document and document["remark"] != "":
                        remarks.append(document["remark"])
                return remarks
            else:
                return ["No Remarks Found."]
        except Exception as e:
            print(e)
            return ["No Remarks found."]
