from Utils.config import meta_collection, users_collection
from Utils.Helpers.AuthManager import AuthManager as am
from flask import jsonify
from bson import ObjectId


class EngagementHelper:
    def __init__(self, user_id):
        self.user_id = user_id

    def update_meta_data(self, user_field, user_value):
        prev_meta = meta_collection.find_one({"user": ObjectId(self.user_id)})
        if prev_meta and prev_meta.get(user_field) == user_value:
            return jsonify({"message": "Value already exists"}), 200

        update = meta_collection.update_one(
            {"user": ObjectId(self.user_id)}, {
                "$set": {user_field: user_value, "lastModifiedBy": ObjectId(am.get_identity())}}
        )
        if update.modified_count == 0:
            update = meta_collection.insert_one(
                {"user": ObjectId(self.user_id), user_field: user_value, "lastModifiedBy": ObjectId(am.get_identity())}
            )
            if update.inserted_id is None:
                return jsonify({"error": "Something Went Wrong"}), 400

        return jsonify({"message": "User updated successfully"}), 200

    def update_user_data(self, user_field, user_value):
        update = users_collection.update_one(
            {"_id": ObjectId(self.user_id)}, {"$set": {user_field: user_value, "lastModifiedBy": ObjectId(am.get_identity())}}
        )
        if update.modified_count == 0:
            return jsonify({"error": "Something Went Wrong"}), 500
        return jsonify({"message": "User updated successfully"}), 200
