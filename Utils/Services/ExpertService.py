from Utils.Helpers.ExpertManager import ExpertManager as em
from Utils.Helpers.UserManager import UserManager as um
from Utils.Helpers.CallManager import CallManager as cm
from Utils.Helpers.AuthManager import AuthManager as am
from flask import jsonify, request, Response
from Utils.config import (
    deleted_experts_collection,
    categories_collection,
    statuslogs_collection,
    experts_collection,
    calls_collection,
    experts_cache,
    subscribers,
)
from datetime import datetime
from bson import ObjectId
import queue
import time
import pytz


class ExpertService:
    """
    A class for managing expert profiles and SSE connections.
    """

    """
        Create a new expert profile in the database with a default name and profile completion status.
        @return The ID of the newly created expert profile.
    """
    @staticmethod
    def create_expert():
        expert = experts_collection.insert_one(
            {
                "name": "Enter Name",
                "categories": [],
                "proflieCompleted": True,
            }
        )
        return jsonify(str(expert.inserted_id))

    """
    A static method to retrieve popup data for a specific expert ID.
    @param expertId - The ID of the expert for whom the popup data is being retrieved.
    @return JSON response containing user context, remarks, and repetition information.
    """
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

    """
    Handle the fetch,edit and deletion of an expert from the database based on the provided ID.
    @param id - The ID of the expert to be deleted
    @return A JSON response indicating the success or failure of the opearation
    """
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
            category_names = []
            if expert["categories"]:
                for category_id in expert["categories"]:
                    category = categories_collection.find_one(
                        {"_id": ObjectId(category_id)})
                    category_name = category["name"] if category else ""
                    category_names.append(category_name)
            expert["categories"] = category_names
            return jsonify(expert)
        elif request.method == "PUT":
            expert_data = request.json
            if not expert_data:
                return jsonify({"error": "Missing data"}), 400
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
            if not any(expert_data[field] for field in required_fields):
                return (
                    jsonify(
                        {"error": "At least one field is required for update"}),
                    400,
                )
            update_query = {}
            for field in required_fields:
                if field == "categories":
                    new_categories_object_ids = []
                    for category_name in expert_data[field]:
                        category = categories_collection.find_one(
                            {"name": category_name})
                        category_id = category["_id"] if category else None
                        new_categories_object_ids.append(category_id)
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
            if not updated_expert:
                return jsonify({"error": "Expert not found"}), 404
            updated_expert["_id"] = str(updated_expert["_id"])
            updated_expert["lastModifiedBy"] = str(
                updated_expert["lastModifiedBy"])
            updated_expert["categories"] = []
            for category_id in updated_expert["categories"]:
                category = categories_collection.find_one(
                    {"_id": ObjectId(category_id)})
                category_name = category["name"] if category else ""
                updated_expert["categories"].append(category_name)
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

    """
    Define a static method to handle streaming data for a specific expert ID.
    @return A stream of events for the specified expert ID.
    """
    @staticmethod
    def call_stream():
        expert_id = request.args.get('expertId')
        if not expert_id:
            return jsonify("expertId query parameter is required"), 400

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
                if expert_id_str in subscribers and q in subscribers[expert_id_str]:
                    subscribers[expert_id_str].remove(q)
                raise
            except BrokenPipeError:
                if expert_id_str in subscribers and q in subscribers[expert_id_str]:
                    subscribers[expert_id_str].remove(q)
                raise

        return Response(event_stream(), content_type='text/event-stream')

    """
    Define a static method to watch changes in a MongoDB collection and notify subscribers based on the operation type.
    @return None
    """
    @staticmethod
    def watch_changes():
        with calls_collection.watch([{'$match': {'operationType': {'$in': ['insert', 'update']}}}]) as stream:
            for change in stream:
                if change['operationType'] == 'insert':
                    doc = change['fullDocument']
                    expert_id = str(doc["expert"])
                    if expert_id in subscribers:
                        for subscriber in subscribers[expert_id]:
                            subscriber.put("call started")
                elif change['operationType'] == 'update':
                    doc_id = change['documentKey']['_id']
                    doc = calls_collection.find_one({'_id': doc_id})
                    if not doc:
                        continue
                    expert_id = str(doc["expert"])
                    if expert_id in subscribers:
                        for subscriber in subscribers[expert_id]:
                            subscriber.put("call ended")

    """
    Close all connections to the server-sent events (SSE) for all subscribers.
    This is a static method that does not require an instance of the class.
    It clears all queues for each expert ID and then clears the subscribers dictionary.
    """
    @staticmethod
    def close_sse_connections():
        for expert_id in list(subscribers.keys()):
            for q in subscribers[expert_id]:
                q.put("connection closed")
            subscribers[expert_id].clear()
        subscribers.clear()

    """
    Periodically reset the connections for the SSE (Server-Sent Events) in the ExpertService class.
    This method is a static method.
    It runs an infinite loop where it sleeps for 600 seconds and then closes the SSE connections.
    No parameters are needed.
    This method does not return anything.
    """
    @staticmethod
    def periodic_reset_sse_connections():
        while True:
            time.sleep(600)  # 10 minutes
            ExpertService.close_sse_connections()

    @staticmethod
    def update_status():
        """
        A static method to update the status of an expert based on the provided data.
        @param request.json - The JSON data containing the expertId and status.
        @return JSON response indicating the success or failure of the status update.
        """
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request"}), 400
        expertId = em.decode_expert_jwt(data["expertId"])
        status = data["status"]
        if not expertId:
            return jsonify({"error": "Invalid Token"}), 400

        if status == "online":
            statuslogs_collection.insert_one({
                "expert": ObjectId(expertId),
                status: datetime.now(pytz.utc)
            })
        elif status == "offline":
            onlinetime = statuslogs_collection.find_one(
                {"expert": ObjectId(expertId), "offline": {"$exists": False}},
                sort=[("updatedAt", -1)]
            )
            if not onlinetime:
                return jsonify({"msg": "No online status found"}), 200
            onlinetime = onlinetime["online"] if onlinetime else None
            duration = (datetime.now(pytz.utc) - datetime.strptime(str(onlinetime),
                        "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=pytz.utc)).total_seconds()
            statuslogs_collection.find_one_and_update(
                {"expert": ObjectId(expertId)},
                {"$set": {status: datetime.now(
                    pytz.utc), "duration": int(duration)}},
                sort=[("updatedAt", -1)]
            )

        experts_collection.update_one(
            {"_id": ObjectId(expertId)},
            {"$set": {"status": status}}
        )

        return jsonify({"msg": "Status updated successfully"})
