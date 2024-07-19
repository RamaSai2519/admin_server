from bson import ObjectId
from datetime import timedelta
from flask import request, jsonify
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from Utils.config import userwebhookmessages_collection, users_collection, wafeedback_collection, watemplates_collection


class WAService:
    def __init__(self):
        self.size = None
        self.page = None
        self.offset = None

    def set_pagination_params(self):
        self.size = request.args.get('size', '10')
        self.page = request.args.get('page', 1, type=int)
        self.size, self.offset = self.get_pagination_params(
            self.size, self.page)

    def get_pagination_params(self, size, page):
        if size == "all":
            return "all", 0
        size = int(size)
        offset = (page - 1) * size
        return size, offset

    def get_wa_history(self):
        if request.method != "GET":
            return jsonify({"error": "Invalid request method"}), 404

        self.set_pagination_params()
        query = {"body": {"$ne": None}}
        userwebhookmessages = self.fetch_documents(
            userwebhookmessages_collection, query)
        total_messages = userwebhookmessages_collection.count_documents(query)
        userwebhookmessages = self.enrich_messages(userwebhookmessages)

        return jsonify({
            "data": userwebhookmessages,
            "total": total_messages,
            "page": self.page,
            "pageSize": self.size
        })

    def fetch_documents(self, collection, query):
        if self.size == "all":
            return list(collection.find(query).sort("createdAt", -1))
        return list(collection.find(query).sort("createdAt", -1).skip(self.offset).limit(self.size))

    def enrich_messages(self, messages):
        for message in messages:
            message["_id"] = str(message["_id"])
            message["userId"] = str(message["userId"])
            user = users_collection.find_one(
                {"_id": ObjectId(message["userId"])})
            if user:
                message["userName"] = user.get("name", "")
                message["userNumber"] = user.get("phoneNumber", "")
            else:
                message["userName"] = ""
                message["userNumber"] = ""
        return messages

    def get_feedbacks(self):
        self.set_pagination_params()
        query = {}
        feedbacks = self.fetch_documents(wafeedback_collection, query)
        total_feedbacks = wafeedback_collection.count_documents(query)
        feedbacks = self.enrich_feedbacks(feedbacks)

        return jsonify({
            "data": feedbacks,
            "total": total_feedbacks,
            "page": self.page,
            "pageSize": self.size
        })

    def enrich_feedbacks(self, feedbacks):
        for feedback in feedbacks:
            feedback["_id"] = str(feedback["_id"])
            feedback["userName"] = hf.get_user_name(
                ObjectId(feedback["userId"]))
            feedback["expertName"] = hf.get_expert_name(
                ObjectId(feedback["sarathiId"]))
            feedback["body"] = feedback["body"][2:].replace("_", " ")
        return feedbacks

    def get_templates(self):
        query = {}
        templates = list(watemplates_collection.find(query))
        for template in templates:
            template["_id"] = str(template["_id"])
        return jsonify({
            "data": templates
        })
