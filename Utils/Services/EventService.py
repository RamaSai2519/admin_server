from Utils.config import events_collection, eventconfigs_collection, users_collection, MAIN_BE_URL
from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from flask import jsonify, request
from bson import ObjectId
import requests
import json


class EventService:
    @staticmethod
    def get_events():
        size, offset, page = uf.pagination_helper()

        allEvents = list(eventconfigs_collection.find().sort(
            "createdAt", -1).skip(offset).limit(size))

        for event in allEvents:
            event["expert"] = hf.get_expert_name(
                ObjectId(event["expert"])) if 'expert' in event else ''
        allEvents = list(map(hf.convert_objectids_to_strings, allEvents))
        total = eventconfigs_collection.count_documents({})

        return jsonify({"data": allEvents, "total": total})

    @staticmethod
    def get_all_event_users():
        onFilter = str(request.args.get("filter"))
        size, offset, page = uf.pagination_helper()

        if onFilter == "true":
            signedUpUsers = list(users_collection.find())
            signedUpPhoneNumbers = [user["phoneNumber"]
                                    for user in signedUpUsers]
            query = {"phoneNumber": {"$nin": signedUpPhoneNumbers}}
        else:
            query = {}
        allEventUsers = list(events_collection.find(query).sort(
            "createdAt", -1).skip(offset).limit(size))
        totalUsers = events_collection.count_documents(query)
        allEventUsers = list(
            map(hf.convert_objectids_to_strings, allEventUsers))

        return jsonify({"data": allEventUsers, "total": totalUsers})

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
                    data["isPremiumUserOnly"] = bool(data["isPremiumUserOnly"])
                    response = requests.post(url, data=data)
                    return response.json()
            except Exception as e:
                print(e)
                return jsonify({"error": str(e)}), 400
        else:
            return jsonify({"error": "Invalid request method"}), 405

    def get_slugs(self):
        slugs = list(eventconfigs_collection.find({}, {"slug": 1}))
        for slug in slugs:
            slug["_id"] = str(slug["_id"])

        return jsonify({"data": slugs})
