from Utils.config import eventconfigs_collection, events_collection
from flask import jsonify, request
import json
import requests


class EventService:
    @staticmethod
    def get_events():
        allEvents = list(eventconfigs_collection.find({}, {"_id": 0}))
        return jsonify(allEvents)

    @staticmethod
    def get_users_by_event():
        params = request.args
        slug = params["slug"]
        url = "https://orca-app-du4na.ondigitalocean.app/api/events/listUsersOfEvent"
        payload = json.dumps({"slug": slug})
        headers = {"Content-Type": "application/json"}
        response = requests.request("GET", url, headers=headers, data=payload)
        data = response.json()["data"]
        return data

    @staticmethod
    def get_event():
        params = request.args
        slug = params["slug"]
        event = eventconfigs_collection.find_one({"slug": slug}, {"_id": 0})
        return jsonify(event)
