from flask import request, jsonify
from datetime import datetime
from bson import ObjectId
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.UserManager import UserManager as um
from Utils.Helpers.AuthManager import AuthManager as am
from Utils.config import (
    userwebhookmessages_collection,
    usernotifications_collection,
    deleted_users_collection,
    applications_collection,
    events_collection,
    users_collection,
    meta_collection,
    users_cache,
)


class UserService:
    def __init__(self):
        pass

    def update_document(self, collection, user_id, update_fields):
        update_fields["lastModifiedBy"] = ObjectId(am.get_identity())
        return collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})

    def get_document(self, collection, user_id):
        return collection.find_one({"_id": ObjectId(user_id)})

    def add_lead_remarks(self):
        if request.method != "POST":
            return jsonify({"error": "Invalid request method"}), 404

        data = request.json
        if not data:
            return jsonify({"error": "Missing data"}), 400

        user_id = data["key"]
        value = data["value"]
        update_fields = {"remarks": value}

        for collection in [users_collection, applications_collection, events_collection]:
            if self.get_document(collection, user_id):
                self.update_document(collection, user_id, update_fields)
                return jsonify({"message": "User updated successfully"}), 200

        return jsonify({"error": "User not found"}), 404

    def get_leads(self):
        if request.method == "GET":
            final_data = []

            user_leadsQuery = {"name": {"$exists": False}}
            user_leads = list(
                users_collection.find(
                    user_leadsQuery, {"Customer Persona": 0}
                ).sort("createdDate", -1)
            )
            signedUpUsers = list(users_collection.find())
            signedUpPhoneNumbers = [user["phoneNumber"]
                                    for user in signedUpUsers]

            allEventUsersQuery = {"phoneNumber": {"$nin": signedUpPhoneNumbers},
                                  "hidden": {"$exists": False}}
            allEventUsers = list(events_collection.find(
                allEventUsersQuery).sort("createdAt", -1))

            for user in user_leads:
                user["leadSource"] = "Website"
            for user in allEventUsers:
                user["leadSource"] = "Events"
                user["createdDate"] = user["createdAt"]

            final_data.extend(allEventUsers)
            final_data.extend(user_leads)
            final_data = list(map(hf.convert_objectids_to_strings, final_data))

            def get_created_date(item):
                return item["createdDate"]

            final_data = sorted(
                final_data, key=get_created_date, reverse=True)

            non_leads = users_collection.count_documents(
                {"name": {"$exists": True}}
            )
            return jsonify({
                "data": final_data,
                "totalUsers": non_leads,
            })

        elif request.method == "POST":
            data = request.json
            if not data:
                return jsonify({"error": "Missing data"}), 400

            user_id = data["user"]["_id"]
            source = data["user"]["source"]
            if source == "Users Lead":
                return jsonify({"error": "Invalid source"}), 400

            collections = {
                "Events": events_collection,
                "Saarthi Application": applications_collection
            }

            if source in collections:
                result = self.update_document(
                    collections[source], user_id, {"hidden": True})
                if result.modified_count == 0:
                    return jsonify({"error": f"{source} not found"}), 400

                return jsonify({"message": "Lead deleted successfully"}), 200

            return jsonify({"error": "Invalid source"}), 400

    def handle_user(self, user_id):
        if request.method == "GET":
            user = self.get_document(users_collection, user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404

            user["_id"] = str(user["_id"])
            user["lastModifiedBy"] = str(
                user["lastModifiedBy"]) if "lastModifiedBy" in user else ""
            if "userGameStats" in user:
                user["userGameStats"] = str(user["userGameStats"])

            meta_doc = self.get_document(meta_collection, user_id)
            if meta_doc:
                user["source"] = meta_doc["source"] if "source" in meta_doc else ""

            wa_history = list(usernotifications_collection.find(
                {"userId": ObjectId(user_id), "templateName": {
                    "$exists": True}},
                {"_id": 0, "userId": 0}
            ).sort("createdAt", -1))

            wa_history += list(userwebhookmessages_collection.find(
                {"userId": ObjectId(user_id), "body": {"$ne": None}},
                {"_id": 0, "userId": 0}
            ).sort("createdAt", -1))

            for history in wa_history:
                history["type"] = "Outgoing" if "templateName" in history else "Incoming"

            user["notifications"] = sorted(
                wa_history, key=lambda x: x["createdAt"], reverse=True)
            return jsonify(user), 200

        elif request.method == "PUT":
            user_data = request.json
            if not user_data:
                return jsonify({"error": "Missing data"}), 400

            fields = ["name", "phoneNumber", "city", "birthDate",
                      "isPaidUser", "numberOfCalls", "context", "source",]
            update_query = {
                field: user_data[field] for field in fields if field in user_data}

            if "birthDate" in update_query:
                update_query["birthDate"] = datetime.strptime(
                    update_query["birthDate"], "%Y-%m-%d")
            if "numberOfCalls" in update_query:
                update_query["numberOfCalls"] = int(
                    update_query["numberOfCalls"])
            if "context" in update_query:
                self.update_document(meta_collection, user_id, {
                                     "context": update_query["context"]})
            if "isPaidUser" in update_query:
                update_query["isPaidUser"] = bool(update_query["isPaidUser"])

            if not update_query:
                return jsonify({"error": "At least one field is required for update"}), 400

            admin_id = am.get_identity()
            update_query["lastModifiedBy"] = ObjectId(admin_id)

            result = self.update_document(
                users_collection, user_id, update_query)

            updated_user = self.get_document(users_collection, user_id)
            if not updated_user:
                return jsonify({"error": "User not found"}), 404
            users_cache[ObjectId(user_id)] = updated_user["name"]
            um.updateProfile_status(updated_user)
            updated_user["_id"] = str(updated_user["_id"])
            updated_user["lastModifiedBy"] = str(
                updated_user["lastModifiedBy"]) if "lastModifiedBy" in updated_user else ""
            updated_user["userGameStats"] = str(
                updated_user["userGameStats"]) if "userGameStats" in updated_user else ""
            return jsonify(updated_user), 200

        elif request.method == "DELETE":
            user = self.get_document(users_collection, user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404
            user["lastModifiedBy"] = ObjectId(am.get_identity())
            deleted_users_collection.insert_one(user)
            result = users_collection.delete_one({"_id": ObjectId(user_id)})
            return jsonify({"message": "User deleted successfully"}), 200 if result.deleted_count else jsonify({"error": "User not found"}), 404

        return jsonify({"error": "Invalid request method"}), 404
