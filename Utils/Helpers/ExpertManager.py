from Utils.config import experts_collection, meta_collection, expertlogs_collection, EXPERT_JWT
from Utils.Helpers.FormatManager import FormatManager as fm
from Utils.Helpers.SlackManager import SlackManager
from datetime import datetime
from bson import ObjectId
import pytz
import jwt


class ExpertManager:
    slack_manager = SlackManager()

    @staticmethod
    def get_online_saarthis():
        online_saarthis = experts_collection.find(
            {"status": {"$regex": "online"}}, {"categories": 0}
        ).sort("name", 1)
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

    @staticmethod
    def decode_expert_jwt(token):
        secret_key = EXPERT_JWT if EXPERT_JWT else ""
        try:
            decoded_token = jwt.decode(
                token, secret_key, algorithms=["HS256"])
            return decoded_token["userId"]
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def status_handler(status, expertId):
        expert = experts_collection.find_one({"_id": ObjectId(expertId)})
        if not expert:
            return None
        expertName = expert["name"]
        if status == "online":
            expertlogs_collection.insert_one({
                "expert": ObjectId(expertId),
                status: datetime.now(pytz.utc)
            })
            ExpertManager.slack_manager.send_message(True, expertName, expertId)
        elif status == "offline":
            onlinetime = expertlogs_collection.find_one(
                {"expert": ObjectId(expertId), "offline": {"$exists": False}},
                sort=[("online", -1)]
            )
            if not onlinetime:
                return None
            onlinetime = onlinetime["online"] if onlinetime else None
            duration = (datetime.now(pytz.utc) - datetime.strptime(str(onlinetime),
                        "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=pytz.utc)).total_seconds()
            expertlogs_collection.find_one_and_update(
                {"expert": ObjectId(expertId)},
                {"$set": {status: datetime.now(
                    pytz.utc), "duration": int(duration)}},
                sort=[("online", -1)]
            )
            ExpertManager.slack_manager.send_message(False, expertName, expertId)
        return True
