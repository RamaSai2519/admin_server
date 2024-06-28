from Utils.config import (
    userwebhookmessages_collection,
    usernotifications_collection,
    deleted_users_collection,
    applications_collection,
    events_collection,
    users_collection,
    calls_collection,
    meta_collection,
    users_cache,
)
from Utils.Helpers.UserManager import UserManager as um
from Utils.Helpers.AuthManager import AuthManager as am
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from flask import request, jsonify
from datetime import datetime
from bson import ObjectId


class UserService:
    @staticmethod
    def get_engagement_data():
        meta_fields = ["remarks", "poc", "expert", "status", "userStatus"]
        if request.method == "GET":
            page = int(request.args.get('page', 1))
            size = int(request.args.get('size', 10))
            offset = (page - 1) * size
            time = datetime.now()

            user_data = list(
                users_collection.find(
                    {"role": {"$ne": "admin"}},
                    {"Customer Persona": 0, "lastModifiedBy": 0, "userGameStats": 0}
                ).sort("createdDate", -1).skip(offset).limit(size)
            )

            total_users = users_collection.count_documents(
                {"role": {"$ne": "admin"}})

            for user in user_data:
                user["_id"] = str(user["_id"])
                user["slDays"] = int((time - user["createdDate"]).days)
                user["createdDate"] = str(
                    user['createdDate'].strftime('%d-%m-%Y'))
                if "birthDate" in user and user["birthDate"] is not None:
                    user["birthDate"] = f"{
                        user['birthDate'].strftime('%d-%m-%Y')}"

                last_call = calls_collection.find_one(
                    {"user": ObjectId(
                        user["_id"]), "status": "successfull", "failedReason": ""},
                    {"_id": 0, "initiatedTime": 1, "expert": 1},
                    sort=[("initiatedTime", -1)],
                )
                days_since_last_call = (
                    time - last_call["initiatedTime"]).days if last_call else 0
                user["lastCallDate"] = f"{last_call['initiatedTime'].strftime(
                    '%d-%m-%Y')}" if last_call else "No Calls"
                user["callAge"] = days_since_last_call if last_call else 0
                user["callsDone"] = calls_collection.count_documents(
                    {"user": ObjectId(user["_id"]), "status": "successfull", "failedReason": ""})
                user["callStatus"] = "First call Pending" if user["callsDone"] == 0 else "First call Done" if user[
                    "callsDone"] == 1 else "Second call Done" if user["callsDone"] == 2 else "Third call Done" if user["callsDone"] == 3 else "Engaged"

                user_meta = meta_collection.find_one(
                    {"user": ObjectId(user["_id"])})
                if user_meta:
                    for field in meta_fields:
                        if field in user_meta:
                            user[field] = user_meta[field]
                        else:
                            user[field] = ""
                if user["expert"] == "" if "expert" in user else True:
                    expert = hf.get_expert_name(
                        last_call["expert"]) if last_call else ""
                    user["expert"] = expert if expert else ""
            return jsonify({
                "data": user_data,
                "total": total_users,
                "page": page,
                "pageSize": size
            })
        if request.method == "POST":
            data = request.json
            if not data:
                return jsonify({"error": "Missing data"}), 400
            try:
                user_id = data["key"]
                if not users_collection.find_one({"_id": ObjectId(user_id)}):
                    return jsonify({"error": "User not found"}), 404
                user_field = data["field"]
                user_value = data["value"]
                if user_field in meta_fields:
                    prev_meta = meta_collection.find_one(
                        {"user": ObjectId(user_id)})
                    if prev_meta:
                        if user_field in prev_meta and prev_meta[user_field] == user_value:
                            return jsonify({"message": "Value already exists"}), 200
                    update = meta_collection.update_one(
                        {"user": ObjectId(user_id)}, {
                            "$set": {user_field: user_value}}
                    )
                    if update.modified_count == 0:
                        update = meta_collection.insert_one(
                            {"user": ObjectId(user_id), user_field: user_value}
                        )
                        if update.inserted_id == None:
                            return jsonify({"error": "Something Went Wrong"}), 400
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
    def add_lead_remarks():
        if request.method == "POST":
            data = request.json
            if not data:
                return jsonify({"error": "Missing data"}), 400
            user_id = data["key"]
            value = data["value"]
            if users_collection.find_one({"_id": ObjectId(user_id)}):
                users_collection.update_one(
                    {"_id": ObjectId(user_id)}, {
                        "$set": {"remarks": value}}
                )
                return jsonify({"message": "User updated successfully"}), 200
            elif applications_collection.find_one({"_id": ObjectId(user_id)}):
                applications_collection.update_one(
                    {"_id": ObjectId(user_id)}, {
                        "$set": {"remarks": value}}
                )
                return jsonify({"message": "User updated successfully"}), 200
            elif events_collection.find_one({"_id": ObjectId(user_id)}):
                events_collection.update_one(
                    {"_id": ObjectId(user_id)}, {
                        "$set": {"remarks": value}}
                )
                return jsonify({"message": "User updated successfully"}), 200
            return jsonify({"error": "User not found"}), 404
        return jsonify({"error": "Invalid request method"}), 404

    @staticmethod
    def get_leads():
        if request.method == "GET":
            final_leads = []
            users = list(users_collection.find({}, {"phoneNumber": 1}))
            user_leads = list(
                users_collection.find(
                    {"name": {"$exists": False}, "hidden": {"$exists": False}},
                    {"Customer Persona": 0}).sort("name", 1)
            )
            for user in user_leads:
                final_leads.append(user)
            expert_leads = list(
                applications_collection.find(
                    {"hidden": {"$exists": False}},
                ).sort("name", 1)
            )
            event_leads = list(
                events_collection.find(
                    {"hidden": {"$exists": False}},
                ).sort("name", 1)
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
                evlead["createdDate"] = evlead["createdAt"]
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
                flead["remarks"] = flead["remarks"] if "remarks" in flead else ""
            final_leads = sorted(
                final_leads, key=lambda x: x["createdDate"], reverse=True)
            return jsonify(final_leads)
        elif request.method == "POST":
            data = request.json
            if not data:
                return jsonify({"error": "Missing data"}), 400
            userId = data["user"]["_id"]
            source = data["user"]["source"]
            if source == "Users Lead":
                return jsonify({"error": "Invalid source"}), 400
            if source == "Events":
                result = events_collection.update_one(
                    {"_id": ObjectId(userId)}, {"$set": {"hidden": True}}
                )
                if result.modified_count == 0:
                    return jsonify({"error": "Event not found"}), 400
            elif source == "Saarthi Application":
                result = applications_collection.update_one(
                    {"_id": ObjectId(userId)}, {"$set": {"hidden": True}}
                )
                if result.modified_count == 0:
                    return jsonify({"error": "Application not found"}), 400
            return jsonify({"message": "Lead deleted successfully"}), 200

    @staticmethod
    def handle_user(id):
        if request.method == "GET":
            user = users_collection.find_one(
                {"_id": ObjectId(id)}, {"_id": 0, "userGameStats": 0})
            if not user:
                return jsonify({"error": "User not found"}), 404
            user["lastModifiedBy"] = (
                str(user["lastModifiedBy"]) if "lastModifiedBy" in user else ""
            )
            meta_doc = meta_collection.find_one({"user": ObjectId(id)})
            if meta_doc:
                user["context"] = str(meta_doc["context"]).split(
                    "\n") if "context" in meta_doc else []
                user["source"] = meta_doc["source"] if "source" in meta_doc else ""

            wa_history = []
            usernotifications = list(usernotifications_collection.find(
                {"userId": ObjectId(id), "templateName": {"$exists": True}},
                {"_id": 0, "userId": 0}
            ).sort("createdAt", -1))
            userwebhookmessages = list(userwebhookmessages_collection.find(
                {"userId": ObjectId(id), "body": {"$ne": None}},
                {"_id": 0, "userId": 0}
            ).sort("createdAt", -1))
            wa_history.extend(usernotifications)
            wa_history.extend(userwebhookmessages)
            for history in wa_history:
                if "templateName" in history:
                    history["type"] = "Outgoing"
                else:
                    history["type"] = "Incoming"

            wa_history = sorted(
                wa_history, key=lambda x: x["createdAt"], reverse=True)

            user["notifications"] = wa_history
            return (
                (jsonify(user), 200)
                if user
                else (jsonify({"error": "User not found"}), 404)
            )
        elif request.method == "PUT":
            user_data = request.json
            if not user_data:
                return jsonify({"error": "Missing data"}), 400
            fields = [
                "name",
                "phoneNumber",
                "city",
                "birthDate",
                "numberOfCalls",
                "context",
                "source",
            ]
            if not any(user_data[field] for field in fields):
                return (
                    jsonify(
                        {"error": "At least one field is required for update"}),
                    400,
                )
            update_query = {}
            for field in fields:
                value = user_data[field]
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
            if not updated_user:
                return jsonify({"error": "User not found"}), 404
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
