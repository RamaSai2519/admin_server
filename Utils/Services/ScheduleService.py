import pytz
from bson import ObjectId
from flask import jsonify, request
from datetime import datetime, timedelta
from Utils.Helpers.AuthManager import AuthManager as am
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.ScheduleManager import ScheduleManager as sm
from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from Utils.config import schedules_collection, experts_collection, users_collection


class ScheduleService:
    @staticmethod
    def schedules():
        if request.method == "GET":
            size, offset, page = uf.pagination_helper()
            schedules = list(schedules_collection.find({}, {
                "lastModifiedBy": 0
            }).sort("datetime", -1).skip(offset).limit(size))

            total_schedules = schedules_collection.count_documents({})

            schedules = uf.format_schedules(schedules)
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

            # sm.final_call_job(
            #     record,
            #     expert_id,
            #     user_id,
            #     expert_number,
            #     user_number,
            #     year,
            #     month,
            #     day,
            #     hour,
            #     minute,
            # )
            response = sm.scheduleCall(time, expert_id, user_id)
            print(response)
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
