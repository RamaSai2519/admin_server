from Utils.config import (
    users_collection,
    meta_collection,
    calls_collection,
    users_cache,
)
from Utils.Helpers.ExpertManager import ExpertManager as em
from datetime import datetime


class UserManager:
    @staticmethod
    def updateProfile_status(user):
        if "name" and "phoneNumber" and "city" and "birthDate" in user:
            if (
                "name" != ""
                and "phoneNumber" != ""
                and "city" != ""
                and "birthDate" != ""
            ):
                users_collection.update_one(
                    {"phoneNumber": user["phoneNumber"]},
                    {"$set": {"profileCompleted": True}},
                )


    @staticmethod
    def get_user_context(user_id):
        if meta_collection.find_one({"user": user_id}) is None:
            return "User context not found."
        else:
            try:
                document = meta_collection.find_one({"user": user_id})
                if "context" in document and document["context"] != "":
                    context = str(document["context"])
                    context = context.split("\n")
                    if users_collection.find_one({"_id": user_id}) is not None:
                        user = users_collection.find_one(
                            {"_id": user_id}, {"_id": 0, "phoneNumber": 0}
                        )
                        user_city = user["city"]
                        user_dob = user["birthDate"]
                        user_name = user["name"]
                        user_age = datetime.now().year - user_dob.year
                        personal_info = {
                            "name": user_name if "name" in user else "Unknown",
                            "city": user_city if "city" in user else "Unknown",
                            "age": user_age if "birthDate" in user else "Unknown",
                        }
                    return {"personal_info": personal_info, "context": context}
                else:
                    return "User context not found."
            except Exception as e:
                print(e)
                return "User context not found."

    @staticmethod
    def determine_user_repeation(user_id, expert_id):
        if len(list(calls_collection.find({"user": user_id}))) > 1:
            if (
                len(list(calls_collection.find({"user": user_id, "expert": expert_id})))
                > 1
            ):
                return "You have connected to this user before."
            else:
                calls = list(calls_collection.find({"user": user_id}))
                latest_call = calls[-2]
                last_expert_name = em.get_expert_name(latest_call["expert"])
                return f"The user has spoken to {last_expert_name} in the last session."
        else:
            return "The user is new to the platform."
