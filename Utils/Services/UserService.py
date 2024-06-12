from Utils.config import (
    users_collection,
    deleted_users_collection,
    meta_collection,
    users_cache,
    applications_collection,
    calls_collection,
    events_collection
)
from Utils.Helpers.UserManager import UserManager as um
from Utils.Helpers.AuthManager import AuthManager as am
from flask import request, jsonify
from datetime import datetime
from bson import ObjectId


class UserService:
    @staticmethod
    def get_engagement_data():
        meta_fields = ["remarks", "poc", "saarthi", "status"]
        if request.method == "GET":
            page = int(request.args.get('page'))
            size = int(request.args.get('size'))
            offset = (page - 1) * size
            time = datetime.now()

            user_data = list(
                users_collection.find(
                    {"role": {"$ne": "admin"}},
                    {"Customer Persona": 0, "lastModifiedBy": 0}
                ).sort("createdDate", 1).skip(offset).limit(size)
            )

            total_users = users_collection.count_documents(
                {"role": {"$ne": "admin"}})

            for user in user_data:
                user["_id"] = str(user["_id"])
                user["createdDate"] = f"{user['createdDate'].strftime(
                    '%d-%m-%Y')} / {(time - user['createdDate']).days}"
                if "birthDate" in user and user["birthDate"] is not None:
                    age = int((time - user["birthDate"]).days) // 365
                    user["birthDate"] = f"{
                        user['birthDate'].strftime('%d-%m-%Y')} / {age}"

                last_call = calls_collection.find_one(
                    {"user": ObjectId(user["_id"])},
                    {"_id": 0, "initiatedTime": 1},
                    sort=[("initiatedTime", -1)],
                )
                days_since_last_call = (
                    time - last_call["initiatedTime"]).days if last_call else 0
                user["lastCallDate"] = f"{last_call['initiatedTime'].strftime(
                    '%d-%m-%Y')} / {days_since_last_call}" if last_call else "No Calls"
                user["callsDone"] = calls_collection.count_documents(
                    {"user": ObjectId(user["_id"])})

                user_meta = meta_collection.find_one(
                    {"user": ObjectId(user["_id"])})
                for field in meta_fields:
                    if field in user_meta:
                        user[field] = user_meta[field]
                    else:
                        user[field] = ""

            return jsonify({
                "data": user_data,
                "total": total_users,
                "page": page,
                "pageSize": size
            })
        if request.method == "POST":
            try:
                user_id = request.json["key"]
                if not users_collection.find_one({"_id": ObjectId(user_id)}):
                    return jsonify({"error": "User not found"}), 404
                user_field = request.json["field"]
                user_value = request.json["value"]
                if user_field in meta_fields:
                    update = meta_collection.update_one(
                        {"user": ObjectId(user_id)}, {
                            "$set": {user_field: user_value}}
                    )
                    if update.modified_count == 0:
                        return jsonify({"message": "Value already exists"}), 200
                    return jsonify({"message": "User updated successfully"}), 200
                else:
                    update = users_collection.update_one(
                        {"_id": ObjectId(user_id)}, {
                            "$set": {user_field: user_value}}
                    )
                    if update.modified_count == 0:
                        return jsonify({"error": "Something Went Wrong"}), 500
                return jsonify({"message": "User updated successfully"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        return jsonify({"error": "Invalid request method"}), 404

    @staticmethod
    def get_leads():
        final_leads = []
        users = list(users_collection.find({}, {"phoneNumber": 1}))
        user_leads = list(
            users_collection.find(
                {"name": {"$exists": False}},
                {"Customer Persona": 0}).sort("name", 1)
        )
        for user in user_leads:
            final_leads.append(user)
        expert_leads = list(
            applications_collection.find().sort("name", 1)
        )
        event_leads = list(
            events_collection.find().sort("name", 1)
        )
        for exlead in expert_leads:
            exlead["source"] = "Saarthi Application"
            final_leads.append(exlead)
        for evlead in event_leads:
            if evlead["phoneNumber"] in [flead["phoneNumber"] for flead in final_leads if flead != evlead]:
                continue
            if evlead["phoneNumber"] in [user["phoneNumber"] for user in users]:
                continue
            evlead["source"] = "Events"
            final_leads.append(evlead)
        for flead in final_leads:
            if (flead["phoneNumber"] in [user["phoneNumber"] for user in users] or
               flead["phoneNumber"] in [flead["phoneNumber"] for flead in final_leads if flead != flead]):
                final_leads.remove(flead)
        for flead in final_leads:
            flead["_id"] = str(flead["_id"]) if "_id" in flead else ""
            flead["name"] = flead["name"] if "name" in flead else ""
            flead["source"] = flead["source"] if "source" in flead else "Users Lead"
            flead["lastModifiedBy"] = (
                str(flead["lastModifiedBy"]
                    ) if "lastModifiedBy" in flead else ""
            )
            flead["lastCallDate"] = "No Calls"
            flead["callsDone"] = 0
        final_leads = sorted(final_leads, key=lambda x: x["name"])
        return jsonify(final_leads)

    @staticmethod
    def handle_user(id):
        if request.method == "GET":
            user = users_collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
            user["lastModifiedBy"] = (
                str(user["lastModifiedBy"]) if "lastModifiedBy" in user else ""
            )
            meta_doc = meta_collection.find_one({"user": ObjectId(id)})
            if meta_doc:
                user["context"] = str(meta_doc["context"]).split("\n")
                user["source"] = meta_doc["source"]
            return (
                (jsonify(user), 200)
                if user
                else (jsonify({"error": "User not found"}), 404)
            )
        elif request.method == "PUT":
            user_data = request.json
            fields = [
                "name",
                "phoneNumber",
                "city",
                "birthDate",
                "numberOfCalls",
                "context",
                "source",
            ]
            if not any(user_data.get(field) for field in fields):
                return (
                    jsonify(
                        {"error": "At least one field is required for update"}),
                    400,
                )
            update_query = {}
            for field in fields:
                value = user_data.get(field)
                if value:
                    if field == "birthDate":
                        value = datetime.strptime(value, "%Y-%m-%d")
                    elif field == "numberOfCalls":
                        value = int(value)
                    elif field == "context":
                        value = "\n".join(value)
                        meta_collection.update_one(
                            {"user": ObjectId(id)}, {
                                "$set": {"context": value}}
                        )
                    update_query[field] = value
                    admin_id = am.get_identity()
                    update_query["lastModifiedBy"] = ObjectId(admin_id)
            result = users_collection.update_one(
                {"_id": ObjectId(id)}, {"$set": update_query}
            )
            if result.modified_count == 0:
                return jsonify({"error": "User not found"}), 404
            updated_user = users_collection.find_one(
                {"_id": ObjectId(id)}, {"_id": 0})
            updated_user["lastModifiedBy"] = str(
                updated_user["lastModifiedBy"])
            users_cache[ObjectId(id)] = updated_user["name"]
            um.updateProfile_status(updated_user)
            return jsonify(updated_user)
        elif request.method == "DELETE":
            user = users_collection.find_one({"_id": ObjectId(id)})
            deleted_users_collection.insert_one(user)
            result = users_collection.delete_one({"_id": ObjectId(id)})
            return (
                (jsonify({"message": "User deleted successfully"}), 200)
                if result.deleted_count
                else (jsonify({"error": "User not found"}), 404)
            )
        else:
            return jsonify({"error": "Invalid request method"}), 404
