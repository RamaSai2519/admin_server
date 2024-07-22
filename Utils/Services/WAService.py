import json
import requests
from bson import ObjectId
from pprint import pprint
from flask import request, jsonify
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.config import userwebhookmessages_collection, users_collection, wafeedback_collection, watemplates_collection, cities_cache, users_cache


class WAService:
    def __init__(self):
        self.size = None
        self.page = None
        self.offset = None
        self.userTypes = ["partial", "full", "all"]
        self.waUrl = "https://6x4j0qxbmk.execute-api.ap-south-1.amazonaws.com/main/actions/send_whatsapp"

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
        # users = users_collection.find(query)
        users = [
            {"name": "Rama Sathya Sai", "phoneNumber": "9398036558", "city": "Goa"},
            {"name": "Mayank Dwivedi", "phoneNumber": "9936142128", "city": "Bengaluru"},
        ]
        return list(users)

    def fetch_cities(self, cities):
        finalCities = []
        for city in cities:
            for c in cities_cache:
                if c["_id"] == city:
                    finalCities.append(c["city"])
        return finalCities

    def find_template(self, templateId: str) -> str:
        template = watemplates_collection.find_one(
            {"_id": ObjectId(templateId)})
        if not template:
            return ""
        template = template["name"]
        return template

    def format_input(self, inputs: dict) -> dict:
        output_dict = {}
        for key, value in inputs.items():
            new_key = key.replace('<', '').replace('>', '')
            output_dict[new_key] = value
        return output_dict

    def prepare_payload(self, user: dict, phoneNumber: str, templateId: str, inputs: dict) -> dict:
        template = self.find_template(templateId)
        if template == "":
            return {}
        inputs = self.format_input(inputs)
        if "user_name" in inputs:
            inputs["user_name"] = user["name"] if "name" in user else "User"
        payload = {
            "phone_number": phoneNumber,
            "template_name": template,
            "parameters": inputs
        }
        return payload

    def send_whatsapp_message(self, payload: str) -> requests.Response:
        headers = {'Content-Type': 'application/json'}
        response = requests.request(
            "POST", self.waUrl, headers=headers, data=payload)
        return response

    def create_query(self, data: dict) -> dict:
        cities, usersType = self.validate_send_request(data)
        if usersType:
            if usersType == "all":
                query = {}
            else:
                query = {"name": {"$exists": usersType == "full"}}
        elif cities:
            cities = self.fetch_cities(cities)
            query = {"city": {"$in": cities}}
        else:
            return {}
        return query

    def handle_send(self):
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        query = self.create_query(data)
        users = self.fetch_users(query)
        for user in users:
            phoneNumber = user["phoneNumber"]
            templateId = data["templateId"]
            inputs = data["inputs"]
            payload = self.prepare_payload(
                user, phoneNumber, templateId, inputs)
            if not payload:
                return jsonify({"error": "Invalid template"}), 400
            response = self.send_whatsapp_message(json.dumps(payload))
            # print(payload, "payload")
            # print(response.headers, "headers")
            # print(response.text, "text")
            if response.status_code != 200:
                return jsonify({"error": "Failed to send message"}), 400

        return jsonify({"message": "success"}), 200

    def get_preview(self):
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        query = self.create_query(data)
        users = users_collection.count_documents(query)
        return jsonify({
            "usersCount": users,
        }), 200
