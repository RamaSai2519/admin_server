from asyncio import Timeout
from re import sub
from sqlite3 import Time
from Utils.config import (
    experts_collection,
    categories_collection,
    deleted_experts_collection,
    calls_collection,
    experts_cache,
    subscribers,
)
from Utils.Helpers.ExpertManager import ExpertManager as em
from Utils.Helpers.UserManager import UserManager as um
from Utils.Helpers.CallManager import CallManager as cm
from Utils.Helpers.AuthManager import AuthManager as am
from flask import jsonify, request, Response
from bson import ObjectId
import queue


class ExpertService:
    @staticmethod
    def create_expert():
        expert = experts_collection.insert_one(
            {
                "name": "Enter Name",
                "proflieCompleted": True,
            }
        )
        return jsonify(str(expert.inserted_id))

    @staticmethod
    def get_popup_data(expertId):
        latest_call = cm.get_latest_call(expertId)
        if latest_call is None:
            return jsonify(
                {"userContext": "", "remarks": "No Calls Found", "repeation": ""}
            )
        user_id = latest_call["user"]
        userContext = um.get_user_context(ObjectId(user_id))
        remarks = em.get_expert_remarks(ObjectId(expertId))
        repeation = um.determine_user_repeation(
            ObjectId(user_id), ObjectId(expertId))
        return jsonify(
            {"userContext": userContext, "remarks": remarks, "repeation": repeation}
        )

    @staticmethod
    def handle_expert(id):
        if request.method == "GET":
            expert = experts_collection.find_one({"_id": ObjectId(id)})
            if not expert:
                return jsonify({"error": "Expert not found"}), 404
            expert["_id"] = str(expert["_id"])
            expert["lastModifiedBy"] = (
                str(expert["lastModifiedBy"]
                    ) if "lastModifiedBy" in expert else ""
            )
            category_names = (
                [
                    categories_collection.find_one({"_id": ObjectId(category_id)}).get(
                        "name", ""
                    )
                    for category_id in expert["categories"]
                ]
                if expert.get("categories")
                else []
            )
            expert["categories"] = category_names
            return jsonify(expert)
        elif request.method == "PUT":
            expert_data = request.json
            required_fields = [
                "name",
                "phoneNumber",
                "topics",
                "description",
                "profile",
                "status",
                "languages",
                "score",
                "active",
                "calls_share",
                "repeat_score",
                "total_score",
                "categories",
                "openingGreeting",
                "flow",
                "tonality",
                "timeSplit",
                "timeSpent",
                "userSentiment",
                "probability",
                "closingGreeting",
            ]
            if not any(expert_data.get(field) for field in required_fields):
                return (
                    jsonify(
                        {"error": "At least one field is required for update"}),
                    400,
                )
            update_query = {}
            for field in required_fields:
                if field == "categories":
                    new_categories_object_ids = [
                        categories_collection.find_one(
                            {"name": category_name})["_id"]
                        for category_name in expert_data.get(field, [])
                    ]
                    update_query[field] = new_categories_object_ids
                elif field in expert_data:
                    update_query[field] = (
                        float(expert_data[field])
                        if field in ["calls_share", "score"]
                        else (
                            int(expert_data[field])
                            if field in ["repeat_score", "total_score"]
                            else expert_data[field]
                        )
                    )
                    admin_id = am.get_identity()
                    update_query["lastModifiedBy"] = ObjectId(admin_id)
            result = experts_collection.update_one(
                {"_id": ObjectId(id)}, {"$set": update_query}
            )
            if result.modified_count == 0:
                return jsonify({"error": "Expert not found"}), 404
            updated_expert = experts_collection.find_one({"_id": ObjectId(id)})
            updated_expert["_id"] = str(updated_expert["_id"])
            updated_expert["lastModifiedBy"] = str(
                updated_expert["lastModifiedBy"])
            updated_expert["categories"] = [
                categories_collection.find_one({"_id": ObjectId(category_id)}).get(
                    "name", ""
                )
                for category_id in updated_expert["categories"]
            ]
            experts_cache[ObjectId(id)] = updated_expert["name"]
            return jsonify(updated_expert)
        elif request.method == "DELETE":
            try:
                expert = experts_collection.find_one({"_id": ObjectId(id)})
                deleted_experts_collection.insert_one(expert)
                result = experts_collection.delete_one({"_id": ObjectId(id)})
                if result.deleted_count == 0:
                    return jsonify({"error": "Expert not found"}), 404
                return jsonify({"message": "Expert deleted successfully"})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            return jsonify({"error": "Invalid request method"}), 404

    @staticmethod
    def call_stream():
        expert_id = request.args.get('expertId')
        if not expert_id:
            return "expertId query parameter is required", 400

        expert_id_str = str(expert_id)

        def event_stream():
            q = queue.Queue()
            if expert_id_str not in subscribers:
                subscribers[expert_id_str] = []
            subscribers[expert_id_str].append(q)
            try:
                while True:
                    try:
                        result = q.get()
                        yield f"data: {result}\n\n"
                    except queue.Empty:
                        yield "data: lalala \n\n"
            except GeneratorExit:
                if expert_id_str in subscribers:
                    subscribers[expert_id_str].remove(q)

        return Response(event_stream(), content_type='text/event-stream')

    @staticmethod
    def watch_changes():
        with calls_collection.watch([{'$match': {'operationType': {'$in': ['insert', 'update']}}}]) as stream:
            for change in stream:
                if change['operationType'] == 'insert':
                    doc = change['fullDocument']
                    expert_id = str(doc.get('expert'))
                    if expert_id in subscribers:
                        for subscriber in subscribers[expert_id]:
                            subscriber.put("call started")
                elif change['operationType'] == 'update':
                    doc_id = change['documentKey']['_id']
                    doc = calls_collection.find_one({'_id': doc_id})
                    expert_id = str(doc.get('expert'))
                    if expert_id in subscribers:
                        for subscriber in subscribers[expert_id]:
                            subscriber.put("call ended")
