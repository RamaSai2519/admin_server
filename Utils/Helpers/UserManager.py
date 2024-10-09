from Utils.config import (
    users_collection,
    meta_collection,
    calls_collection,
)
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
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
        if users_collection.find_one({"_id": user_id}) is not None:
            user = users_collection.find_one(
                {"_id": user_id}, {"_id": 0, "phoneNumber": 0}
            )
            if not user:
                return "No user found."
            user_city = user["city"]
            user_dob = user["birthDate"]
            user_name = user["name"]
            user_age = datetime.now().year - user_dob.year
            personal_info = {
                "name": user_name if "name" in user else "Unknown",
                "city": user_city if "city" in user else "Unknown",
                "age": user_age if "birthDate" in user else "Unknown",
            }
            user_persona = (user["customerPersona"]
                            if "customerPersona" in user else "Unknown")
            document = meta_collection.find_one({"user": user_id})
            if not document:
                return {
                    "personal_info": personal_info,
                    "context": ["Unknown"],
                    "persona": user_persona
                }
            if "context" in document:
                context = str(document["context"])
                context = context.split(
                    "\n") if context != "" else "Unknown"
            else:
                context = [""]
            return {
                "personal_info": personal_info,
                "context": context,
                "persona": user_persona,
            }
        else:
            return "No user found."

    @staticmethod
    def determine_user_repeation(user_id, expert_id):
        if len(list(calls_collection.find({"user": user_id, "status": " ", "failedReason": ""}))) > 1:
            if (
                len(list(calls_collection.find(
                    {"user": user_id, "expert": expert_id, "status": "successfull", "failedReason": ""})))
                > 1
            ):
                return "You have connected to this user before."
            else:
                calls = list(calls_collection.find(
                    {"user": user_id,  "status": "successfull", "failedReason": ""}))
                latest_call = calls[-2]
                last_expert_name = hf.get_expert_name(latest_call["expert"])
                return f"The user has spoken to {last_expert_name} in the last session."
        else:
            return "The user is new to the platform."
