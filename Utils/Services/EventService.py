from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.config import eventconfigs_collection, MAIN_BE_URL
from flask import jsonify, request
from bson import ObjectId
from pprint import pprint
import requests
import json


class EventService:
    @staticmethod
    def get_events():
        page = request.args.get("page", 1, type=int)
        limit = request.args.get("limit", 10, type=int)
        offset = (page - 1) * limit

        allEvents = list(eventconfigs_collection.find(
            {}, {"_id": 0}).sort("createdAt", -1).skip(offset).limit(limit)
        )

        for event in allEvents:
            event["lastModifiedBy"] = (
                str(event["lastModifiedBy"]
                    ) if "lastModifiedBy" in event else ""
            )
            event["expert"] = hf.get_expert_name(
                ObjectId(event["expert"])) if 'expert' in event else ''
        total = eventconfigs_collection.count_documents({})

        return jsonify({"data": allEvents, "total": total})

    @staticmethod
    def get_users_by_event():
        url = f"{MAIN_BE_URL}/events/listUsersOfEvent"
        params = request.args
        headers = {
            'Content-Type': 'application/json'
        }
        if "slug" not in params:
            response = requests.request("GET", url, headers=headers)
            data = response.json()["data"]
            return data
        slug = params["slug"]
        payload = json.dumps({
            "slug": slug
        })
        response = requests.request("GET", url, headers=headers, data=payload)
        data = response.json()["data"]
        return data

    @staticmethod
    def handle_event_config():
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
            try:
                data = request.json
                if not data:
                    return jsonify({"error": "Invalid request"}), 400
                url = f"{MAIN_BE_URL}/events/validateSlug"
                params = {"slug": data["slug"]}
                payload = json.dumps(params)
                response = requests.request("GET", url, data=payload)
                validSlug = response.json()
                validSlug = validSlug["data"]["isSlugAvailable"]
                if not validSlug:
                    return jsonify({"error": "Slug already exists"}), 400
                else:
                    url = f"{MAIN_BE_URL}/events/config"
                    response = requests.post(url, data=data)
                    return response.json()
            except Exception as e:
                print(e)
                return jsonify({"error": str(e)}), 400
        else:
            return jsonify({"error": "Invalid request method"}), 405
