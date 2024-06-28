from Utils.Helpers.EventManager import EventManager as evm
from Utils.Helpers.AuthManager import AuthManager as am
from Utils.config import eventconfigs_collection
from datetime import datetime, timedelta
from flask import jsonify, request
from bson import ObjectId
import requests
import json


class EventService:
    @staticmethod
    def get_events():
        allEvents = list(eventconfigs_collection.find({}, {"_id": 0}))
        for event in allEvents:
            event["lastModifiedBy"] = (
                str(event["lastModifiedBy"]
                    ) if "lastModifiedBy" in event else ""
            )
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
            event = eventconfigs_collection.find_one(
                {"slug": slug}, {"_id": 0})
            if not event:
                return jsonify({"error": "Event not found"}), 404
            event["lastModifiedBy"] = (
                str(event["lastModifiedBy"]
                    ) if "lastModifiedBy" in event else ""
            )
            return jsonify(event)
        elif request.method == "POST":
            data = request.json
            if not data:
                return jsonify({"error": "Missing data"}), 400
            fields = ["date", "duration", "expert", "mainTitle",
                      "name", "slug", "subTitle", "zoomLink", "imageUrl"]
            if not all(data[field] for field in fields):
                return (
                    jsonify({"error": "All fields are required for create"}),
                    400,
                )
            slug = data["slug"]
            if eventconfigs_collection.find_one({"slug": slug}):
                return jsonify({"message": "Event already exists"}), 400
            data["date"] = datetime.strptime(
                data["date"], "%Y-%m-%dT%H:%M:%S.%fZ")
            data["validUpto"] = data["date"] + timedelta(hours=5, minutes=30)
            createdTime = datetime.now()
            data["createdAt"] = createdTime
            data["updatedAt"] = createdTime
            admin_id = am.get_identity()
            data["lastModifiedBy"] = ObjectId(admin_id)
            result = eventconfigs_collection.insert_one(data)
            if result.inserted_id is None:
                return jsonify({"error": "Failed to create event"}), 400
            return jsonify({"message": "Event created successfully"}), 200
        elif request.method == "PUT":
            data = request.json
            if not data:
                return jsonify({"error": "Missing data"}), 400
            fields = ["name", "mainTitle", "subTitle", "imageUrl"]
            if not any(data[field] for field in fields):
                return (
                    jsonify(
                        {"error": "At least one field is required for update"}),
                    400,
                )
            event = evm.update_event(data, fields)
            return jsonify(event)
