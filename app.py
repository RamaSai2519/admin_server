from email.utils import parsedate_to_datetime
from pymongo import MongoClient, DESCENDING
from excluded_users import excluded_users
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
from firebase_admin import credentials
from flask_cors import CORS
from bson import ObjectId
import firebase_admin
import requests
import pytz
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

client = MongoClient(
    "mongodb+srv://sukoon_user:Tcks8x7wblpLL9OA@cluster0.o7vywoz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["test"]
calls_collection = db["calls"]
experts_collection = db["experts"]
users_collection = db["users"]
fcm_tokens_collection = db["fcm_tokens"]
logs_collection = db["errorlogs"]
categories_collection = db["categories"]
statuslogs_collection = db["statuslogs"]
blogs_collection = db["blogposts"]
applications_collection = db["becomesaarthis"]
schedules_collection = db["schedules"]

calls_collection.create_index([("initiatedTime", DESCENDING)])
users_collection.create_index([("createdDate", DESCENDING)])
experts_collection.create_index([("createdDate", DESCENDING)])
experts_collection.create_index([("status", 1)])

users_cache = {}
experts_cache = {}
call_threads = {}


# def call_at_specified_time(time, expert, user, thread_name):
#     scheduled_time = datetime.strptime(time, r"%Y-%m-%dT%H:%M:%S.%fZ").replace(
#         tzinfo=pytz.utc
#     )
#     current_time = datetime.now(pytz.utc)
#     delay = scheduled_time - current_time
#     if delay.total_seconds() > 0 and call_threads[thread_name]:
#         sleep(delay.total_seconds())
#         call_intiator(expert, user)


# def call_intiator(expert_number, user_number):
#     url = "https://kpi.knowlarity.com/Basic/v1/account/call/makecall"
#     payload = {
#         "k_number": "+918035384523",
#         "agent_number": "+91" + expert_number,
#         "customer_number": "+91" + user_number,
#         "caller_id": "+918035384523",
#     }
#     headers = {
#         "x-api-key": "bb2S4y2cTvaBVswheid7W557PUzUVMnLaPnvyCxI",
#         "authorization": "0738be9e-1fe5-4a8b-8923-0fe503e87deb",
#     }
#     response = requests.post(url, json=payload, headers=headers)

#     return response.json()


def get_timedelta(duration_str):
    try:
        hours, minutes, seconds = map(int, duration_str.split(":"))
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    except ValueError:
        return timedelta(seconds=0)


def is_valid_duration(duration_str):
    parts = duration_str.split(":")
    if len(parts) == 3:
        try:
            hours, minutes, seconds = map(int, parts)
            if 0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60:
                return True
        except ValueError:
            pass
    return False


def format_call(call):
    user_id = call.get("user", "Unknown")
    expert_id = call.get("expert", "Unknown")
    call["_id"] = str(call.get("_id", ""))
    call["userName"] = get_user_name(user_id)
    call["user"] = str(user_id)
    call["expertName"] = get_expert_name(expert_id)
    call["expert"] = str(expert_id)
    call["ConversationScore"] = call.pop("Conversation Score", 0)
    if call.get("failedReason") == "call missed":
        call["status"] = "missed"
    if call.get("status") == "successfull":
        call["status"] = "successful"
    return call


def get_user_name(user_id):
    if user_id in users_cache:
        return users_cache[user_id]
    user = users_collection.find_one({"_id": user_id}, {"name": 1})
    if user:
        if user.get("name"):
            users_cache[user_id] = user["name"]
            return user["name"]
    return "Unknown"


def get_expert_name(expert_id):
    if expert_id in experts_cache:
        return experts_cache[expert_id]
    expert = experts_collection.find_one({"_id": expert_id}, {"name": 1})
    if expert:
        experts_cache[expert_id] = expert["name"]
        return expert["name"]
    return "Unknown"


def send_push_notification(token, message):
    fcm_url = "https://fcm.googleapis.com/fcm/send"
    server_key = "AAAAM5jkbNg:APA91bG80zQ8CzD1AeQmV45YT4yWuwSgJ5VwvyLrNynAJBk4AcyCb6vbCSGlIQeQFPAndS0TbXrgEL8HFYQq4DMXmSoJ4ek7nFcCwOEDq3Oi5Or_SibSpywYFrnolM4LSxpRkVeiYGDv"
    payload = {
        "to": token,
        "notification": {"title": "Notification", "body": message},
    }
    headers = {"Authorization": "key=" + server_key, "Content-Type": "application/json"}
    response = requests.post(fcm_url, json=payload, headers=headers)
    if response.status_code == 200:
        pass
    else:
        print("Failed to send notification:", response.text)


def get_formatted_expert(expert):
    expert_id = str(expert["_id"])
    login_logs = list(
        statuslogs_collection.find({"expert": expert_id, "status": "online"})
    )

    logged_in_hours = calculate_logged_in_hours(login_logs)

    formatted_expert = {
        "_id": expert_id,
        "name": expert.get("name", "Unknown"),
        "phoneNumber": expert.get("phoneNumber", ""),
        "score": expert.get("score", 0),
        "status": expert.get("status", "offline"),
        "createdDate": expert.get("createdDate", ""),
        "loggedInHours": logged_in_hours,
        "repeatRate": expert.get("repeat_score", 0),
        "callsShare": expert.get("calls_share", 0),
        "totalScore": expert.get("total_score", 0),
    }

    return formatted_expert


def get_calls(query={}):
    calls = list(calls_collection.find(query, {"_id": 0}).sort([("initiatedTime", 1)]))
    calls = [format_call(call) for call in calls]
    return calls


@socketio.on("error_notification")
def handle_error_notification(data):
    utc_now = datetime.now(pytz.utc)
    ist_timezone = pytz.timezone("Asia/Kolkata")
    ist_now = utc_now.astimezone(ist_timezone)
    time = ist_now.strftime("%Y-%m-%d %H:%M:%S")
    document = {"message": data, "time": time}
    logs_collection.insert_one(document)
    emit("error_notification", data, broadcast=True)
    tokens = list(fcm_tokens_collection.find())
    for token in tokens:
        token["_id"] = str(token.get("_id", ""))
        send_push_notification(token["token"], data)


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
    calls = get_calls({"user": {"$nin": excluded_users}})
    return jsonify(calls)


@app.route("/api/new-calls")
def get_new_calls():
    timestamp = request.args.get("timestamp")
    timestamp = parsedate_to_datetime(timestamp)
    timestamp = timestamp + timedelta(seconds=1)
    new_calls = get_calls({"initiatedTime": {"$gte": timestamp}})
    return jsonify(new_calls)


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
    users = list(users_collection.find({"_id": {"$nin": excluded_users}}))
    for user in users:
        user["_id"] = str(user.get("_id", ""))
    return jsonify(users)


@app.route("/api/new-users")
def get_new_users():
    timestamp = request.args.get("timestamp")
    timestamp = parsedate_to_datetime(timestamp)
    timestamp = timestamp + timedelta(seconds=1)
    new_users = list(users_collection.find({"createdDate": {"$gt": timestamp}}))
    for user in new_users:
        user["_id"] = str(user.get("_id", ""))
    return jsonify(new_users)


@app.route("/api/users/<string:id>", methods=["GET", "PUT"])
def handle_user(id):
    if request.method == "GET":
        user = users_collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user)
    elif request.method == "PUT":
        user_data = request.json
        new_name = user_data.get("name")
        new_phone_number = user_data.get("phoneNumber")
        new_city = user_data.get("city")
        new_birth_date = user_data.get("birthDate")
        new_number_of_calls = user_data.get("numberOfCalls")
        if not any(
            [new_name, new_phone_number, new_city, new_birth_date, new_number_of_calls]
        ):
            return jsonify({"error": "At least one field is required for update"}), 400
        update_query = {}
        if new_name:
            update_query["name"] = new_name
        if new_phone_number:
            update_query["phoneNumber"] = new_phone_number
        if new_city:
            update_query["city"] = new_city
        if new_birth_date:
            new_birth_date = datetime.strptime(new_birth_date, "%Y-%m-%d")
            update_query["birthDate"] = new_birth_date
        if new_number_of_calls:
            update_query["numberOfCalls"] = int(new_number_of_calls)
        result = users_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": update_query}
        )
        if result.modified_count == 0:
            return jsonify({"error": "User not found"}), 404
        updated_user = users_collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
        users_cache.pop(id, None)
        return jsonify(updated_user)


@app.route("/api/experts")
def get_experts():
    experts = list(experts_collection.find({}, {"categories": 0}))
    formatted_experts = [get_formatted_expert(expert) for expert in experts]
    return jsonify(formatted_experts)


@app.route("/api/new-experts")
def get_new_experts():
    timestamp = request.args.get("timestamp")
    timestamp = parsedate_to_datetime(timestamp)
    timestamp = timestamp + timedelta(seconds=1)
    new_experts = list(experts_collection.find({"createdDate": {"$gt": timestamp}}))
    formatted_new_experts = [get_formatted_expert(expert) for expert in new_experts]
    return jsonify(formatted_new_experts)


@app.route("/api/experts/<string:id>", methods=["GET", "PUT"])
def handle_expert(id):
    if request.method == "GET":
        expert = experts_collection.find_one({"_id": ObjectId(id)})
        if not expert:
            return jsonify({"error": "Expert not found"}), 404
        expert["_id"] = str(expert.get("_id", ""))
        category_names = []
        for category_id in expert.get("categories", []):
            category = categories_collection.find_one({"_id": ObjectId(category_id)})
            if category:
                category_names.append(category.get("name", ""))
        expert["categories"] = category_names
        return jsonify(expert)
    elif request.method == "PUT":
        expert_data = request.json
        new_name = expert_data.get("name")
        new_phone_number = expert_data.get("phoneNumber")
        new_topics = expert_data.get("topics")
        new_description = expert_data.get("description")
        new_profile = expert_data.get("profile")
        new_status = expert_data.get("status")
        new_languages = expert_data.get("languages")
        new_calls_share = expert_data.get("calls_share")
        new_score = expert_data.get("score")
        new_repeat_score = expert_data.get("repeat_score")
        new_total_score = expert_data.get("total_score")
        new_categories_names = expert_data.get("categories")
        new_opening = expert_data.get("openingGreeting")
        new_flow = expert_data.get("flow")
        new_tonality = expert_data.get("tonality")
        new_timeSplit = expert_data.get("timeSplit")
        new_timeSpent = expert_data.get("timeSpent")
        new_sentiment = expert_data.get("userSentiment")
        new_probability = expert_data.get("probability")
        new_closing = expert_data.get("closingGreeting")
        if not any(
            [
                new_name,
                new_phone_number,
                new_topics,
                new_description,
                new_profile,
                new_status,
                new_languages,
                new_score,
                new_calls_share,
                new_repeat_score,
                new_total_score,
                new_categories_names,
                new_opening,
                new_flow,
                new_tonality,
                new_timeSplit,
                new_sentiment,
                new_probability,
                new_closing,
                new_timeSpent,
            ]
        ):
            return jsonify({"error": "At least one field is required for update"}), 400
        update_query = {}
        if new_name:
            update_query["name"] = new_name
        if new_phone_number:
            update_query["phoneNumber"] = new_phone_number
        if new_topics:
            update_query["topics"] = new_topics
        if new_description:
            update_query["description"] = new_description
        if new_profile:
            update_query["profile"] = new_profile
        if new_calls_share:
            update_query["calls_share"] = float(new_calls_share)
        if new_status:
            update_query["status"] = new_status
        if new_languages:
            update_query["languages"] = new_languages
        if new_score:
            update_query["score"] = float(new_score)
        if new_repeat_score:
            update_query["repeat_score"] = int(new_repeat_score)
        if new_total_score:
            update_query["total_score"] = int(new_total_score)
        if new_categories_names:
            new_categories_object_ids = []
            for category_name in new_categories_names:
                category = categories_collection.find_one({"name": category_name})
                if category:
                    new_categories_object_ids.append(category["_id"])
            update_query["categories"] = new_categories_object_ids
        if new_opening:
            update_query["openingGreeting"] = float(new_opening)
        if new_closing:
            update_query["closingGreeting"] = float(new_closing)
        if new_flow:
            update_query["flow"] = float(new_flow)
        if new_tonality:
            update_query["tonality"] = float(new_tonality)
        if new_timeSplit:
            update_query["timeSplit"] = float(new_timeSplit)
        if new_timeSpent:
            update_query["timeSpent"] = float(new_timeSpent)
        if new_sentiment:
            update_query["userSentiment"] = float(new_sentiment)
        if new_probability:
            update_query["probability"] = float(new_probability)
        result = experts_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": update_query}
        )
        if result.modified_count == 0:
            return jsonify({"error": "Expert not found"}), 404
        updated_expert = experts_collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
        category_names = []
        for category_id in updated_expert.get("categories", []):
            category = categories_collection.find_one({"_id": ObjectId(category_id)})
            if category:
                category_names.append(category.get("name", ""))
        updated_expert["categories"] = category_names
        return jsonify(updated_expert)


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
            "datetime": ist_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "status": "pending",
        }
        schedules_collection.insert_one(document)
        time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ")
        hour = ist_time.hour - 1
        minute = ist_time.minute
        year = ist_time.year
        month = ist_time.month - 1
        day = ist_time.day

        # print(hour, minute, year, month, day)

        expert_docment = experts_collection.find_one({"_id": ObjectId(expert_id)})
        expert_number = expert_docment.get("phoneNumber", "")
        # expert_name = expert_docment.get("name", "")

        user_name = users_collection.find_one({"_id": ObjectId(user_id)}, {"name": 1})
        user_name = user_name.get("name", "")
        user_number = user_name.get("PhoneNumber", "")

        record = schedules_collection.find_one(document, {"_id": 1})
        record = str(record.get("_id", ""))
        # scheduleJob(
        #     expert_name,
        #     user_name,
        #     year,
        #     month,
        #     day,
        #     hour,
        #     minute,
        #     expert_number,
        #     record,
        # )
        FinalCallJob(record, expert_number, user_number, year, month, day, hour, minute)
        return jsonify({"message": "Data received successfully"})
    else:
        return jsonify({"error": "Invalid request method"}), 404


def scheduleJob(
    expert_name, user_name, year, month, day, hour, minute, expert_number, record
):
    url = "http://15.206.127.248:8080/api/v1/scheduleJob"
    payload = {
        "saarthiName": expert_name,
        "userName": user_name,
        "istHour": hour,
        "istMinute": minute,
        "year": year,
        "month": month,
        "day": day,
        "year": year,
        "link": f"https://admin-sukoon.vercel.app/approve/{record}",
        "recordId": record,
        "saarthiNumber": expert_number,
        "adminNumber": "9398036558",
        "superAdminNumber": "9398036558",
    }
    print(payload)
    requests.post(url, json=payload)


@app.route("/api/schedule/<id>", methods=["PUT", "DELETE", "GET"])
def update_schedule(id):
    if request.method == "PUT":
        try:
            data = request.json
            expert = data.get("expert")
            expert = experts_collection.find_one({"name": expert}, {"_id": 1})
            expert = str(expert.get("_id"))
            user = data.get("user")
            user = users_collection.find_one({"name": user}, {"_id": 1})
            user = str(user.get("_id"))
            time = data.get("datetime")

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

            if result.modified_count == 0:
                return jsonify({"error": "Failed to update schedule"}), 400

            return jsonify({"message": "Schedule updated successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == "DELETE":
        try:
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


def cancelJob(record, level):
    url = "http://15.206.127.248:8080/api/v1/cancelJob"
    if level == "0":
        payload = {"recordIds": [f"{record}-1", f"{record}-2"]}
    elif level == "1":
        payload = {"recordIds": [f"{record}-0", f"{record}-2"]}
    else:
        payload = {"recordIds": [f"{record}-0", f"{record}-1"]}

    requests.post(url, json=payload)


def FinalCallJob(record, expert_number, user_number, year, month, day, hour, minute):
    url = "http://15.206.127.248:8080/api/v1/scheduleFinalCall"
    payload = {
        "requestId": record,
        "expertNumber": expert_number,
        "userNumber": user_number,
        "year": year,
        "month": month - 1,
        "day": day,
        "hour": hour,
        "minute": minute - 1,
    }
    requests.post(url, json=payload)


@app.route("/api/approve/<id>/<level>", methods=["PUT"])
def approve_application(id, level):
    data = request.json
    status = data.get("status")
    cancelJob(id, level)
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
    FinalCallJob(
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


def calculate_logged_in_hours(login_logs):
    total_logged_in_hours = 0
    last_logged_out_time = None

    for log in login_logs:
        if log["status"] == "online":
            logged_in_at = log["date"]
            logged_out_at = (
                datetime.now() if last_logged_out_time is None else last_logged_out_time
            )
        else:
            logged_out_at = log["date"]
            logged_in_at = last_logged_out_time
        if logged_in_at is not None and logged_out_at is not None:
            total_logged_in_hours += (
                logged_out_at - logged_in_at
            ).total_seconds() / 3600
        last_logged_out_time = logged_out_at

    return total_logged_in_hours


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=80,
        debug=True,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )
