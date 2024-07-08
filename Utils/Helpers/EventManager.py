from Utils.Helpers.AuthManager import AuthManager as am
from Utils.config import eventconfigs_collection
from datetime import datetime
from bson import ObjectId


class EventManager:
    @staticmethod
    def update_event(data, fields):
        update_query = {}
        for field in fields:
            if data[field] != data["slug"]:
                update_query[field] = data[field]
        updatedTime = datetime.now()
        update_query["updatedAt"] = updatedTime
        admin_id = am.get_identity()
        update_query["lastModifiedBy"] = ObjectId(admin_id)
        eventconfigs_collection.update_one(
            {"slug": data["slug"]}, {"$set": update_query}
        )
        return eventconfigs_collection.find_one({"slug": data["slug"]}, {"_id": 0, "lastModifiedBy": 0})
