from Utils.config import (
    deleted_schedules_collection,
    fcm_tokens_collection,
    schedules_collection,
    experts_collection,
    users_collection,
    ALLOWED_MIME_TYPES,
    s3_client
)
from Utils.Helpers.ScheduleManager import ScheduleManager as sm
from Utils.Helpers.InsightsManager import InsightsManager as im
from Utils.Helpers.AuthManager import AuthManager as am
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask import request, jsonify
from bson import ObjectId
import pytz
import uuid
import os


class AppService:
    @staticmethod
    def get_insights():
        callInsights = im.create_insights_structures()
        return jsonify(callInsights)

    @staticmethod
    def save_fcm_token():
        data = request.json
        if not data:
            return jsonify({"error": "FCM token missing"}), 400
        token = data["token"]
        tokens = list(fcm_tokens_collection.find())
        if token in [t["token"] for t in tokens]:
            return jsonify({"message": "FCM token already saved"}), 200
        elif token:
            fcm_tokens_collection.insert_one({"token": token})
            return jsonify({"message": "FCM token saved successfully"}), 200
        else:
            return jsonify({"error": "FCM token missing"}), 400

    @staticmethod
    def update_schedule(id):
        if request.method == "PUT":
            try:
                data = request.json
                if not data:
                    return jsonify({"error": "Data missing"}), 400
                expert = data["expert"]
                expert = experts_collection.find_one({"name": expert})
                if not expert:
                    return jsonify({"error": "Expert not found"}), 404
                expert_number = expert["phoneNumber"] if "phoneNumber" in expert else ""
                expert = str(expert["_id"])
                user = data["user"]
                user = users_collection.find_one({"name": user})
                if not user:
                    return jsonify({"error": "User not found"}), 404
                user_number = user["phoneNumber"]
                user = str(user["_id"])
                time = data["datetime"]
                ist_offset = timedelta(hours=5, minutes=30)
                date_object = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
                ist_time = date_object + ist_offset

                sm.cancel_final_call(id)
                admin_id = am.get_identity()
                result = schedules_collection.update_one(
                    {"_id": ObjectId(id)},
                    {
                        "$set": {
                            "lastModifiedBy": ObjectId(admin_id),
                            "expert": ObjectId(expert),
                            "user": ObjectId(user),
                            "datetime": time,
                        }
                    },
                )
                time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
                hour = ist_time.hour - 1
                minute = ist_time.minute
                year = ist_time.year
                month = ist_time.month - 1
                day = ist_time.day

                sm.final_call_job(
                    result,
                    expert,
                    user,
                    expert_number,
                    user_number,
                    year,
                    month,
                    day,
                    hour,
                    minute,
                )
                if result.modified_count == 0:
                    return jsonify({"error": "Failed to update schedule"}), 400

                return jsonify({"message": "Schedule updated successfully"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        elif request.method == "DELETE":
            try:
                schedule = schedules_collection.find_one({"_id": ObjectId(id)})
                deleted_schedules_collection.insert_one(schedule)
                result = schedules_collection.delete_one({"_id": ObjectId(id)})
                sm.cancel_final_call(id)
                if result.deleted_count == 0:
                    return jsonify({"error": "Schedule not found"}), 404
                return jsonify({"message": "Schedule deleted successfully"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        elif request.method == "GET":
            schedule = schedules_collection.find_one({"_id": ObjectId(id)})
            if not schedule:
                return jsonify({"error": "Schedule not found"}), 404
            schedule["_id"] = (str(schedule["_id"]),)
            expert_id = (schedule["expert"],)
            expert = experts_collection.find_one(
                {"_id": expert_id}, {"name": 1})
            schedule["expert"] = expert["name"] if expert else ""
            user_id = schedule["user"]
            user = users_collection.find_one({"_id": user_id}, {"name": 1})
            schedule["user"] = user["name"] if user else ""
            timestamp_utc = datetime.strptime(
                schedule["datetime"], "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            ist_timezone = pytz.timezone("Asia/Kolkata")
            timestamp_ist = timestamp_utc.astimezone(ist_timezone)
            schedule["datetime"] = timestamp_ist.strftime(r"%Y-%m-%d %H:%M:%S")
            return jsonify(schedule)

    @staticmethod
    def approve_application(id, level):
        data = request.json
        if not data:
            return jsonify({"error": "Data missing"}), 400
        status = data["status"]
        sm.cancel_final_call(id, level)  # type: ignore
        result = schedules_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": {"status": status}}
        )
        schedule_record = schedules_collection.find_one({"_id": ObjectId(id)})
        if not schedule_record:
            return jsonify({"error": "Application not found"}), 404
        expert_id = schedule_record["expert"]
        expert = experts_collection.find_one({"_id": expert_id})
        if not expert:
            return jsonify({"error": "Expert not found"}), 404
        expert_number = expert["phoneNumber"]
        user_id = schedule_record["user"]
        user = users_collection.find_one({"_id": user_id})
        if not user:
            return jsonify({"error": "User not found"}), 404
        user_number = user["phoneNumber"]
        scheduled_Call_time = schedule_record["datetime"]
        scheduled_Call_time = datetime.strptime(
            scheduled_Call_time, "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        sm.final_call_job(
            result,
            expert_id,
            user_id,
            expert_number,
            user_number,
            scheduled_Call_time.year,
            scheduled_Call_time.month - 1,
            scheduled_Call_time.day,
            scheduled_Call_time.hour - 1,
            scheduled_Call_time.minute,
        )
        if result.modified_count == 0:
            return jsonify({"error": "Application not found"}), 404
        return jsonify({"message": "Application updated successfully"}), 200

    @staticmethod
    def file_filter(mimetype):
        return mimetype in ALLOWED_MIME_TYPES

    @staticmethod
    def upload():
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if not AppService.file_filter(file.mimetype):
            return jsonify({"error": "Invalid file type"}), 400

        try:
            story_id = str(uuid.uuid4())
            filename = secure_filename(file.filename).replace(   # type: ignore
                " ", "+")
            unique_filename = f"{int(os.times()[-1])}_{story_id}_{filename}"

            metadata = {
                "fieldName": file.name.lower().replace(" ", "+")  # type: ignore
            }

            s3_client.upload_fileobj(
                file,
                "sukoon-media",
                unique_filename,
                ExtraArgs={
                    "ACL": "public-read",
                    "Metadata": metadata,
                    "ContentType": file.mimetype
                }
            )

            file_url = f"{
                s3_client.meta.endpoint_url}/sukoon-media/{unique_filename}"

            return jsonify({"message": "File uploaded successfully", "file_url": file_url})

        except Exception as e:
            return jsonify({"error": str(e)}), 500
