from Utils.Helpers.EventManager import EventManager as evm
from Utils.config import eventconfigs_collection
from flask import jsonify, request
from datetime import datetime
import requests
import json


class EventService:
    @staticmethod
    def get_events():
        allEvents = list(eventconfigs_collection.find({}, {"_id": 0}))
        return jsonify(allEvents)

    @staticmethod
    def get_users_by_event():
        try:
            url = (
                "https://orca-app-du4na.ondigitalocean.app/api/events/listUsersOfEvent"
            )
            headers = {"Content-Type": "application/json"}
            if request.args:
                params = request.args
                slug = params["slug"]
                payload = json.dumps({"slug": slug})
                response = requests.get(url, headers=headers, data=payload)
            else:
                response = requests.get(url, headers=headers)
            data = response.json()["data"]
            return data
        except Exception as e:
            print(e)
            return jsonify({"error": str(e)})

    @staticmethod
    def get_event():
        if request.method == "GET":
            params = request.args
            slug = params["slug"]
            event = eventconfigs_collection.find_one({"slug": slug}, {"_id": 0})
            return jsonify(event)
        elif request.method == "POST":
            data = request.json
            fields = ["name", "mainTitle", "subTitle"]
            if not all(data[field] for field in fields):
                return (
                    jsonify({"error": "All fields are required for create"}),
                    400,
                )
            slug = data["slug"]
            if eventconfigs_collection.find_one({"slug": slug}):
                event = evm.update_event(data, fields)
                return jsonify(event)
            createdTime = datetime.now()
            data["createdAt"] = createdTime
            data["updatedAt"] = createdTime
            eventconfigs_collection.insert_one(data)
            event = eventconfigs_collection.find_one({"slug": slug}, {"_id": 0})
            return jsonify(event)
        elif request.method == "PUT":
            data = request.json
            fields = ["name", "mainTitle", "subTitle"]
            if not any(data[field] for field in fields):
                return (
                    jsonify({"error": "At least one field is required for update"}),
                    400,
                )
            event = evm.update_event(data, fields)
            return jsonify(event)
