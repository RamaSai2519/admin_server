from Utils.config import experts_collection, meta_collection, EXPERT_JWT
from Utils.Helpers.FormatManager import FormatManager as fm
import jwt


class ExpertManager:
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