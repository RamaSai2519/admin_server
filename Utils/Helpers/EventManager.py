from Utils.config import eventconfigs_collection
from datetime import datetime


class EventManager:
    @staticmethod
    def update_event(data, fields):
        update_query = {}
        for field in fields:
            if data[field] != data["slug"]:
                update_query[field] = data[field]
        updatedTime = datetime.now()
        update_query["updatedAt"] = updatedTime
        eventconfigs_collection.update_one(
            {"slug": data["slug"]}, {"$set": update_query}
        )
        return eventconfigs_collection.find_one({"slug": data["slug"]}, {"_id": 0})
