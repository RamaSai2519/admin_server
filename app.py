from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from flask_cors import CORS
from bson import ObjectId
from functions import *
import pytz

app = Flask(__name__)
CORS(app)


@app.route("/api/blogs")
def get_blogs():
    blogs = list(blogs_collection.find({}, {"_id": 0}))
    return jsonify(blogs)


@app.route("/api/blogs/<string:id>", methods=["GET"])
def get_blog(id):
    blog = blogs_collection.find_one({"id": id})
    blog["_id"] = str(blog["_id"])
    return jsonify(blog)


@app.route("/api/featuredblog")
def get_featured_blog():
    featured_blog = blogs_collection.find_one(sort=[("id", -1)])
    featured_blog["_id"] = str(featured_blog["_id"])
    return jsonify(featured_blog)


@app.route("/api/save-fcm-token", methods=["POST"])
def save_fcm_token():
    data = request.json
    token = data.get("token")
    tokens = list(fcm_tokens_collection.find())
    if token in [t["token"] for t in tokens]:
        return jsonify({"message": "FCM token already saved"}), 200
    elif token:
        fcm_tokens_collection.insert_one({"token": token})
        return jsonify({"message": "FCM token saved successfully"}), 200
    else:
        return jsonify({"error": "FCM token missing"}), 400


@app.route("/api/leads", methods=["GET"])
def get_leads():
    final_leads = []
    leads = list(users_collection.find({}, {"Customer Persona": 0}))
    for lead in leads:
        if lead.get("profileCompleted") is False:
            lead["_id"] = str(lead.get("_id", ""))
            lead["createdDate"] = lead.get("createdDate", "")
            final_leads.append(lead)
    return jsonify(final_leads)


@app.route("/api/errorlogs")
def get_error_logs():
    error_logs = list(logs_collection.find())
    for log in error_logs:
        log["_id"] = str(log.get("_id", ""))
    return jsonify(error_logs)


@app.route("/api/applications")
def get_applications():
    applications = list(applications_collection.find())
    for application in applications:
        application["_id"] = str(application.get("_id", ""))
    return jsonify(applications)


@app.route("/api/calls")
def get_calls_route():
    calls = get_calls({}, {})
    return jsonify(calls)


@app.route("/api/calls/<string:id>", methods=["GET", "PUT"])
def handle_call(id):
    if (request.method) == "GET":
        call = calls_collection.find_one({"callId": id})
        if not call:
            return jsonify({"error": "Call not found"}), 404
        formatted_call = format_call(call)
        return jsonify(formatted_call)
    elif (request.method) == "PUT":
        data = request.get_json()
        new_conversation_score = data.get("ConversationScore")
        result = calls_collection.update_one(
            {"callId": id},
            {"$set": {"Conversation Score": float(new_conversation_score)}},
        )

        if result.modified_count == 0:
            return jsonify({"error": "Failed to update Conversation Score"}), 400
        else:
            return jsonify(new_conversation_score), 200


@app.route("/api/users")
def get_users():
    users = list(
        users_collection.find(
            {"role": {"$ne": "admin"}, "name": {"$exists": True}},
            {"name": {"$exists": True}},
            {"Customer Persona": 0},
        )
    )
    for user in users:
        user["_id"] = str(user.get("_id", ""))
        user["createdDate"] = user.get("createdDate", "").strftime("%Y-%m-%d")
    return jsonify(users)


@app.route("/api/users/<string:id>", methods=["GET", "PUT", "DELETE"])
def handle_user(id):
    if request.method == "GET":
        user = users_collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
        return (
            (jsonify(user), 200)
            if user
            else (jsonify({"error": "User not found"}), 404)
        )
    elif request.method == "PUT":
        user_data = request.json
        fields = ["name", "phoneNumber", "city", "birthDate", "numberOfCalls"]
        if not any(user_data.get(field) for field in fields):
            return jsonify({"error": "At least one field is required for update"}), 400
        update_query = {}
        for field in fields:
            value = user_data.get(field)
            if value:
                if field == "birthDate":
                    value = datetime.strptime(value, "%Y-%m-%d")
                elif field == "numberOfCalls":
                    value = int(value)
                update_query[field] = value

        result = users_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": update_query}
        )
        if result.modified_count == 0:
            return jsonify({"error": "User not found"}), 404
        users_cache.pop(id, None)
        updated_user = users_collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
        updateProfile_status(updated_user)
        return jsonify(updated_user)
    elif request.method == "DELETE":
        result = users_collection.delete_one({"_id": ObjectId(id)})
        return (
            (jsonify({"message": "User deleted successfully"}), 200)
            if result.deleted_count
            else (jsonify({"error": "User not found"}), 404)
        )
    else:
        return jsonify({"error": "Invalid request method"}), 404


@app.route("/api/dashboard/stats")
def get_dashboard_stats():
    current_date = datetime.now(pytz.timezone("Asia/Kolkata"))
    today_start = datetime.combine(current_date, datetime.min.time())
    today_end = datetime.combine(current_date, datetime.max.time())
    total_calls = len(get_calls())
    today_calls_query = {"initiatedTime": {"$gte": today_start, "$lt": today_end}}
    today_calls = get_calls(today_calls_query, {})
    today_successful_calls = sum(
        1 for call in today_calls if call["status"] == "successful"
    )
    today_total_calls = len(today_calls)
    online_saarthis = get_online_saarthis()
    total_successful_calls, total_duration_seconds = (
        get_total_successful_calls_and_duration()
    )
    average_call_duration = (
        format_duration(total_duration_seconds / total_successful_calls)
        if total_successful_calls
        else "0 minutes"
    )

    total_failed_calls = total_calls - total_successful_calls
    today_failed_calls = today_total_calls - today_successful_calls

    stats_data = {
        "totalCalls": total_calls,
        "successfulCalls": total_successful_calls,
        "todayCalls": today_total_calls,
        "failedCalls": total_failed_calls,
        "todayFailedCalls": today_failed_calls,
        "todaySuccessfulCalls": today_successful_calls,
        "averageCallDuration": average_call_duration,
        "onlineSaarthis": online_saarthis,
    }

    return jsonify(stats_data)


@app.route("/api/experts")
def get_experts():
    experts = list(experts_collection.find({}, {"categories": 0}))
    formatted_experts = [get_formatted_expert(expert) for expert in experts]
    return jsonify(formatted_experts)


@app.route("/api/experts/<string:id>", methods=["GET", "PUT", "DELETE"])
def handle_expert(id):
    if request.method == "GET":
        expert = experts_collection.find_one({"_id": ObjectId(id)})
        if not expert:
            return jsonify({"error": "Expert not found"}), 404
        expert["_id"] = str(expert.get("_id", ""))
        category_names = [
            categories_collection.find_one({"_id": ObjectId(category_id)}).get(
                "name", ""
            )
            for category_id in expert.get("categories", [])
        ]
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
            return jsonify({"error": "At least one field is required for update"}), 400
        update_query = {}
        for field in required_fields:
            if field == "categories":
                new_categories_object_ids = [
                    categories_collection.find_one({"name": category_name}).get("_id")
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
        result = experts_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": update_query}
        )
        if result.modified_count == 0:
            return jsonify({"error": "Expert not found"}), 404
        updated_expert = experts_collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
        updated_expert["categories"] = [
            categories_collection.find_one({"_id": ObjectId(category_id)}).get(
                "name", ""
            )
            for category_id in updated_expert.get("categories", [])
        ]
        return jsonify(updated_expert)
    elif request.method == "DELETE":
        result = experts_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Expert not found"}), 404
        return jsonify({"message": "Expert deleted successfully"})
    else:
        return jsonify({"error": "Invalid request method"}), 404


@app.route("/api/categories")
def get_categories():
    categories = list(categories_collection.find({}, {"_id": 0, "name": 1}))
    category_names = [category["name"] for category in categories]
    return jsonify(category_names)


@app.route("/api/schedule", methods=["POST", "GET"])
def schedule_route():
    if request.method == "GET":
        schedules = list(schedules_collection.find())
        for schedule in schedules:
            schedule["_id"] = str(schedule.get("_id", ""))
            expert_id = schedule.get("expert", "")
            expert_id = experts_collection.find_one({"_id": expert_id}, {"name": 1})
            schedule["expert"] = expert_id.get("name", "") if expert_id else ""
            user_id = schedule.get("user", "")
            user_id = users_collection.find_one({"_id": user_id}, {"name": 1})
            schedule["user"] = user_id.get("name", "") if user_id else ""
            if isinstance(schedule.get("datetime"), datetime):
                schedule["datetime"] = schedule.get("datetime", "").strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        return jsonify(schedules)
    elif request.method == "POST":
        data = request.json
        expert_id = data.get("expert")
        user_id = data.get("user")
        time = data.get("datetime")
        ist_offset = timedelta(hours=5, minutes=30)
        date_object = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
        ist_time = date_object + ist_offset

        document = {
            "expert": ObjectId(expert_id),
            "user": ObjectId(user_id),
            "datetime": ist_time,
            "status": "pending",
        }
        schedules_collection.insert_one(document)
        time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
        hour = ist_time.hour
        minute = ist_time.minute
        year = ist_time.year
        month = ist_time.month - 1
        day = ist_time.day

        expert_docment = experts_collection.find_one({"_id": ObjectId(expert_id)})
        expert_number = expert_docment.get("phoneNumber", "")

        user = users_collection.find_one({"_id": ObjectId(user_id)})
        user_number = user.get("phoneNumber", "")

        record = schedules_collection.find_one(document, {"_id": 1})
        record = str(record.get("_id", ""))
        final_call_job(
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


@app.route("/api/schedule/<id>", methods=["PUT", "DELETE", "GET"])
def update_schedule(id):
    if request.method == "PUT":
        try:
            data = request.json
            expert = data.get("expert")
            expert = experts_collection.find_one({"name": expert})
            expert = str(expert.get("_id"))
            expert_number = expert.get("phoneNumber", "")
            user = data.get("user")
            user = users_collection.find_one({"name": user})
            user_number = user.get("phoneNumber", "")
            user = str(user.get("_id"))
            time = data.get("datetime")
            ist_offset = timedelta(hours=5, minutes=30)
            date_object = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
            ist_time = date_object + ist_offset

            cancel_final_call(id)

            result = schedules_collection.update_one(
                {"_id": ObjectId(id)},
                {
                    "$set": {
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

            final_call_job(
                id, expert_number, user_number, year, month, day, hour, minute
            )

            if result.modified_count == 0:
                return jsonify({"error": "Failed to update schedule"}), 400

            return jsonify({"message": "Schedule updated successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "DELETE":
        try:
            cancel_final_call(id)
            result = schedules_collection.delete_one({"_id": ObjectId(id)})
            if result.deleted_count == 0:
                return jsonify({"error": "Schedule not found"}), 404
            return jsonify({"message": "Schedule deleted successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "GET":
        schedule = schedules_collection.find_one({"_id": ObjectId(id)})
        if not schedule:
            return jsonify({"error": "Schedule not found"}), 404
        schedule["_id"] = str(schedule.get("_id", ""))
        expert_id = schedule.get("expert", "")
        expert = experts_collection.find_one({"_id": expert_id}, {"name": 1})
        schedule["expert"] = expert.get("name", "") if expert else ""
        user_id = schedule.get("user", "")
        user = users_collection.find_one({"_id": user_id}, {"name": 1})
        schedule["user"] = user.get("name", "") if user else ""
        timestamp_utc = datetime.strptime(
            schedule.get("datetime", ""), "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        ist_timezone = pytz.timezone("Asia/Kolkata")
        timestamp_ist = timestamp_utc.astimezone(ist_timezone)
        schedule["datetime"] = timestamp_ist.strftime(r"%Y-%m-%d %H:%M:%S")
        return jsonify(schedule)


@app.route("/api/approve/<id>/<level>", methods=["PUT"])
def approve_application(id, level):
    data = request.json
    status = data.get("status")
    cancel_final_call(id, level)
    result = schedules_collection.update_one(
        {"_id": ObjectId(id)}, {"$set": {"status": status}}
    )
    schedule_record = schedules_collection.find_one({"_id": ObjectId(id)})
    expert_id = schedule_record.get("expert", "")
    expert = experts_collection.find_one({"_id": expert_id})
    expert_number = expert.get("phoneNumber", "")
    user_id = schedule_record.get("user", "")
    user = users_collection.find_one({"_id": user_id})
    user_number = user.get("phoneNumber", "")
    scheduled_Call_time = schedule_record.get("datetime", "")
    scheduled_Call_time = datetime.strptime(
        scheduled_Call_time, "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    final_call_job(
        id,
        expert_number,
        user_number,
        scheduled_Call_time.year,
        scheduled_Call_time.month,
        scheduled_Call_time.day,
        scheduled_Call_time.hour,
        scheduled_Call_time.minute,
    )
    if result.modified_count == 0:
        return jsonify({"error": "Application not found"}), 404
    return jsonify({"message": "Application updated successfully"}), 200


if __name__ == "__main__":
    Flask.run(app, port=8080)
