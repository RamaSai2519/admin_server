import json
import requests
import threading
from bson import ObjectId
from datetime import datetime
from flask import request, jsonify
from Utils.Helpers.WAHelper import WAHelper
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.config import userwebhookmessages_collection, users_collection, wafeedback_collection, watemplates_collection, cities_cache, temp_collection, events_collection, eventconfigs_collection


class WAService:
    def __init__(self):
        self.size = None
        self.page = None
        self.offset = None
        self.userTypes = ["partial", "full", "all"]
        self.wa_helper = WAHelper()

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

    def validate_send_request(self, data):
        usersType = data["usersType"]
        cities = data["cities"]

        if not usersType and not cities:
            return jsonify({"error": "Neither User Type or User Cities are provided"}), 400
        if usersType and usersType not in self.userTypes:
            return jsonify({"error": "Invalid User Type"}), 400
        if usersType and cities:
            return jsonify({"error": "Both User Type and User Cities are provided"}), 400
        return cities, usersType

    def fetch_users(self, query: dict) -> list:
        users = users_collection.find(query)
        return list(users)

    def create_query(self, data: dict) -> dict:
        cities, usersType = self.validate_send_request(data)
        query = {"wa_opt_out": False}
        if usersType:
            if usersType != "all":
                query["profileCompleted"] = usersType == "full"
        elif cities:
            query["city"] = {"$in": cities}
        else:
            return query
        return query

    def handle_send(self):
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400

        if data["usersType"] == "event" and not data["eventSlug"]:
            return jsonify({"error": "Event slug is required"}), 200

        if data["usersType"] == "event":
            event = eventconfigs_collection.find_one(
                {"_id": ObjectId(data["eventSlug"])})
            users = events_collection.find({"source": event["slug"]})
        else:
            query = self.create_query(data)
            users = self.fetch_users(query)

        messageId = data["messageId"]

        def final_send():
            for user in users:
                templateId = data["templateId"]
                inputs = data["inputs"]
                payload = self.wa_helper.prepare_payload(
                    user=user, templateId=templateId, inputs=inputs)
                if not payload:
                    return jsonify({"error": "Invalid template"}), 400
                self.wa_helper.send_whatsapp_message(
                    payload, messageId, phoneNumber=user["phoneNumber"])
        threading.Thread(target=final_send).start()

        return jsonify({"message": "success"}), 200

    def get_preview(self):
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400

        if data["usersType"] == "event" and not data["eventSlug"]:
            return jsonify({"error": "Event slug is required"}), 200

        if data["usersType"] == "event":
            event = eventconfigs_collection.find_one(
                {"_id": ObjectId(data["eventSlug"])})
            users = events_collection.count_documents(
                {"source": event["slug"]})
        else:
            query = self.create_query(data)
            users = users_collection.count_documents(query)

        return jsonify({
            "usersCount": users,
        }), 200

    def fetchStatus(self):
        messageId = request.args.get("messageId")
        proNum = request.args.get("proNum")
        if not messageId:
            return jsonify({"error": "Invalid request data"}), 400
        query = {"messageId": messageId}
        count = temp_collection.count_documents(query)
        if count == proNum:
            status = "done"
        else:
            status = "pending"
        return jsonify({"data": {
            "status": status,
            "count": count
        }}), 200
