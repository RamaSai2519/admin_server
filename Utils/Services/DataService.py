from Utils.config import (
    userwebhookmessages_collection,
    applications_collection,
    wafeedback_collection,
    categories_collection,
    errorlogs_collection,
    schedules_collection,
    experts_collection,
    timings_collection,
    users_collection
)
from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.ScheduleManager import ScheduleManager as sm
from Utils.Helpers.FormatManager import FormatManager as fm
from Utils.Helpers.AuthManager import AuthManager as am
from datetime import datetime, timedelta
from flask import jsonify, request
from bson import ObjectId
import pytz


class DataService:
    """
    A class that provides static methods to retrieve data.
    - get_error_logs(): Retrieves error logs from a collection, converts the '_id' field to a string, and returns the logs as JSON.
    - get_applications(): Processes feedback data by getting the expert name, modifying the body text, and returns the feedbacks data along with total count, page, and page size as JSON.
    - get_all_calls(): Retrieves all calls data from a collection and returns the calls data as JSON.
    - get_experts(): Retrieves experts data from a collection, formats the data, and returns the experts data as JSON.
    - get_users(): Retrieves users data from a collection, modifies the '_id', 'lastModifiedBy', 'createdDate', and 'userGameStats' fields, and returns the users data as JSON.
    - get_categories(): Retrieves categories data from a collection, extracts the 'name' field, and returns the category names as JSON.
    - schedules(): Retrieves schedules data from a collection, modifies the '_id', 'expert', and 'user' fields, and returns the schedules data as JSON.
    - get_slots(): Retrieves slots data from a collection, processes the data, and returns the slots data as JSON.
    - get_timings(): Retrieves timings data from a collection, processes the data, and returns the timings data as JSON.
    - get_wa_history(): Retrieves WhatsApp history data from a collection, processes the data, and returns the WhatsApp history data as JSON.
    - get_feedbacks(): Retrieves feedbacks data from a collection, processes the data, and returns the feedbacks data as JSON.
    """
    @staticmethod
    def get_error_logs():
        error_logs = list(errorlogs_collection.find())
        for log in error_logs:
            log["_id"] = str(log["_id"])
        return jsonify(error_logs)

    @staticmethod
    def get_applications():
        applications = list(applications_collection.find())
        for application in applications:
            application["_id"] = str(application["_id"])
        return jsonify(applications)

    @staticmethod
    def get_all_calls():
        return uf.get_calls()

    @staticmethod
    def get_experts():
        experts = list(experts_collection.find(
            {}, {"categories": 0}).sort("name", 1))
        formatted_experts = [fm.get_formatted_expert(
            expert) for expert in experts]
        return jsonify(formatted_experts)

    @staticmethod
    def get_users():
        users = list(
            users_collection.find(
                {"role": {"$ne": "admin"}, "profileCompleted": True,
                    "city": {"$exists": True}},
                {"Customer Persona": 0},
            )
        )
        for user in users:
            user["_id"] = str(user["_id"])
            user["lastModifiedBy"] = (
                str(user["lastModifiedBy"]) if "lastModifiedBy" in user else ""
            )
            user["createdDate"] = user["createdDate"].strftime("%Y-%m-%d")
            user["userGameStats"] = (
                str(user["userGameStats"]) if "userGameStats" in user else ""
            )
        return jsonify(users)

    @staticmethod
    def get_categories():
        if request.method == "GET":
            categories = list(categories_collection.find(
                {}, {"_id": 0, "name": 1}))
            category_names = [category["name"] for category in categories]
            return jsonify(category_names)
        elif request.method == "POST":
            data = request.json
            if not data:
                return jsonify({"error": "Invalid request data"}), 400
            category = data["name"]
            createdDate = datetime.now()
            categories_collection.insert_one(
                {"name": category, "createdDate": createdDate, "active": True}
            )
            return jsonify({"message": "Category added successfully"})

    @staticmethod
    def schedules():
        if request.method == "GET":
            page = int(request.args.get('page', 1))
            size = int(request.args.get('size', 10))
            offset = (page - 1) * size

            schedules = list(schedules_collection.find({}, {
                "lastModifiedBy": 0
            }).sort("datetime", -1).skip(offset).limit(size))

            total_schedules = schedules_collection.count_documents({})

            for schedule in schedules:
                schedule["_id"] = str(schedule["_id"])
                schedule["expert"] = hf.get_expert_name(schedule["expert"])
                schedule["user"] = hf.get_user_name(schedule["user"])
            return jsonify({
                "data": schedules,
                "total": total_schedules
            })
        elif request.method == "POST":
            data = request.json
            if not data:
                return jsonify({"error": "Invalid request data"}), 400
            user_id = data["user"]
            time = data["datetime"]
            expert_id = data["expert"]
            try:
                admin_id = ObjectId(am.get_identity())
            except Exception:
                admin_id = ObjectId("665b5b5310b36290eaa59d27")
            type = data["type"] if "type" in data else "User"
            duration = data["duration"] if "duration" in data else 30

            ist_offset = timedelta(hours=5, minutes=30)
            date_object = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
            ist_time = date_object + ist_offset

            document = {
                "expert": ObjectId(expert_id),
                "user": ObjectId(user_id),
                "lastModifiedBy": admin_id,
                "type": type,
                "datetime": ist_time,
                "status": "pending",
                "duration": int(duration),
            }
            schedules_collection.insert_one(document)
            time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
            hour = ist_time.hour
            minute = ist_time.minute
            year = ist_time.year
            month = ist_time.month - 1
            day = ist_time.day

            expert_docment = experts_collection.find_one(
                {"_id": ObjectId(expert_id)})
            expert_number = expert_docment["phoneNumber"] if expert_docment else ""

            user = users_collection.find_one({"_id": ObjectId(user_id)})
            user_number = user["phoneNumber"] if user and "phoneNumber" in user else ""

            record = schedules_collection.find_one(document, {"_id": 1})

            record = str(record["_id"]) if record else ""

            sm.final_call_job(
                record,
                expert_id,
                user_id,
                expert_number,
                user_number,
                year,
                month,
                day,
                hour,
                minute,
            )
            return jsonify({"message": "Data received successfully"})
        else:
            return jsonify({"error": "Invalid request method"}), 404

    @ staticmethod
    def get_slots():
        # Parse input data
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        expert_id = data["expert"]
        utc_date = data["datetime"]
        duration = int(data["duration"])
        expert_doc = experts_collection.find_one(
            {"_id": ObjectId(expert_id)}, {"type": 1})
        expert_type = expert_doc["type"] if expert_doc else None

        # Convert UTC datetime to IST and extract the day
        utc_datetime = datetime.strptime(utc_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        ist_datetime = utc_datetime + timedelta(hours=5, minutes=30)
        day_name = ist_datetime.strftime("%A")

        # Calculate available slots
        slots = sm.slots_calculater(expert_id, day_name, duration)
        if not slots:
            return jsonify([])

        output_slots = []
        utc_zone = pytz.utc
        ist_timezone = pytz.timezone('Asia/Kolkata')

        # Iterate through the slots
        for slot in slots:
            slot_start_str = slot.split(' - ')[0]
            slot_start_time = datetime.strptime(slot_start_str, "%H:%M").time()

            slot_start_ist = datetime.combine(
                ist_datetime.date(), slot_start_time)
            slot_start_utc = (slot_start_ist - timedelta(hours=5, minutes=30)
                              # Make slot_start_utc timezone-aware
                              ).replace(tzinfo=utc_zone)
            slot_start_utc_str = slot_start_utc.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ")

            slot_dict = {
                "slot": slot,
                "datetime": slot_start_utc_str,
                "available": slot_start_utc >= datetime.now(utc_zone)
            }
            output_slots.append(slot_dict)

            # Check for expert's schedule
            if slot_dict["available"]:
                expert_schedule = schedules_collection.find_one({
                    "expert": ObjectId(expert_id),
                    "datetime": {
                        "$gte": slot_start_ist,
                        "$lt": slot_start_ist + timedelta(minutes=duration)
                    }
                })

                if expert_schedule:
                    scheduled_duration = expert_schedule["duration"] if "duration" in expert_schedule else 60
                    if scheduled_duration in [30, 60]:
                        slot_dict["available"] = False
                        if scheduled_duration == 60:
                            next_slot = slots[slots.index(slot) + 1]
                            slots.remove(next_slot)

                utc_datetime = datetime.strptime(
                    slot_dict["datetime"], '%Y-%m-%dT%H:%M:%S.%fZ')
                ist_datetime = utc_datetime.astimezone(ist_timezone)
                ist_hour = ist_datetime.hour

                if expert_type and expert_type == "saarthi" or "sarathi":
                    if not (9 <= ist_hour < 22):
                        slot_dict["available"] = False
                else:
                    if not (10 <= ist_hour < 14) or not (16 <= ist_hour < 20):
                        slot_dict["available"] = False

        return jsonify(output_slots)

    @staticmethod
    def get_timings():
        if request.method == "GET":
            expertId = request.args.get("expert")
            timings = list(timings_collection.find({
                "expert": ObjectId(expertId)
            }))
            for timing in timings:
                timing["_id"] = str(timing["_id"])
                timing["expert"] = str(timing["expert"])
            return jsonify(timings)
        if request.method == "POST":
            data = request.json
            if not data:
                return jsonify({"error": "Invalid request data"}), 400
            expertId = data["expertId"]
            field = data["row"]["field"]
            value = data["row"]["value"]

            fields = [
                "PrimaryStartTime",
                "PrimaryEndTime",
                "SecondaryStartTime",
                "SecondaryEndTime",
            ]
            if field not in fields:
                return jsonify({"error": "Invalid field"}), 400
            try:
                timing = timings_collection.find_one({
                    "expert": ObjectId(expertId)
                })

                if timing:
                    timings_collection.update_one({"expert": ObjectId(expertId)}, {
                                                  "$set": {field: value}})
                    return jsonify({"message": "Timing updated successfully"})
                else:
                    timings_collection.insert_one(
                        {"expert": ObjectId(expertId), field: value})
                    return jsonify({"message": "Timing added successfully"})
            except Exception as e:
                print(e)
                return jsonify({"error": str(e)}), 400

    @staticmethod
    def get_wa_history():
        if request.method == "GET":
            size = request.args.get('size', '10')
            page = request.args.get('page', '1')

            try:
                size = int(size)
                page = int(page)
                offset = (page - 1) * size
            except ValueError:
                offset = 0
                size = "all"

            if size != "all":
                userwebhookmessages = list(userwebhookmessages_collection.find(
                    {"body": {"$ne": None}}
                ).sort("createdAt", -1).skip(int(offset)).limit(int(size)))
            else:
                userwebhookmessages = list(userwebhookmessages_collection.find(
                    {"body": {"$ne": None}}
                ).sort("createdAt", -1))

            total_messages = userwebhookmessages_collection.count_documents(
                {"body": {"$ne": None}}
            )

            for message in userwebhookmessages:
                message["_id"] = str(message["_id"])
                message["userId"] = str(message["userId"])
                message["createdAt"] = (message["createdAt"] + timedelta(
                    hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                user = users_collection.find_one(
                    {"_id": ObjectId(message["userId"])})
                if user:
                    message["userName"] = user["name"] if "name" in user else ""
                    message["userNumber"] = user["phoneNumber"] if "phoneNumber" in user else ""
                else:
                    message["userName"] = ""
                    message["userNumber"] = ""
            return jsonify({
                "data": userwebhookmessages,
                "total": total_messages,
                "page": page,
                "pageSize": size
            })
        else:
            return jsonify({"error": "Invalid request method"}), 404

    @ staticmethod
    def get_feedbacks():
        size = request.args.get('size', '10')
        page = request.args.get('page', '1')

        try:
            size = int(size)
            page = int(page)
            offset = (page - 1) * size
        except ValueError:
            offset = 0
            size = "all"

        if size != "all":
            feedbacks = list(wafeedback_collection.find({}).sort(
                "createdAt", -1).skip(offset).limit(size))
        else:
            feedbacks = list(wafeedback_collection.find(
                {}).sort("createdAt", -1))

        total_feedbacks = wafeedback_collection.count_documents({})

        for feedback in feedbacks:
            feedback["_id"] = str(feedback["_id"])
            feedback["createdAt"] = (feedback["createdAt"] + timedelta(
                hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            feedback["userName"] = hf.get_user_name(
                ObjectId(feedback["userId"]))
            feedback["expertName"] = hf.get_expert_name(
                ObjectId(feedback["sarathiId"]))
            feedback["body"] = feedback["body"][2:]
            feedback["body"] = str(feedback["body"]).replace("_", " ")

        return jsonify({
            "data": feedbacks,
            "total": total_feedbacks,
            "page": page,
            "pageSize": size
        })
