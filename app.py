from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from pymongo import MongoClient, DESCENDING
from flask_cors import CORS
from email.utils import parsedate_to_datetime
from bson import ObjectId
import pytz
from datetime import datetime, timedelta
import requests
import firebase_admin
from firebase_admin import credentials
from excluded_users import excluded_users

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

calls_collection.create_index([("initiatedTime", DESCENDING)])
users_collection.create_index([("createdDate", DESCENDING)])
experts_collection.create_index([("createdDate", DESCENDING)])
experts_collection.create_index([("status", 1)])

users_cache = {}
experts_cache = {}


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
        "totalScore": expert.get("total_score", 0)
    }

    return formatted_expert


def get_calls(query={}):
    calls = list(calls_collection.find(query, {"_id": 0}).sort([("initiatedTime", 1)]))
    calls = [format_call(call) for call in calls]
    return calls

@socketio.on("error_notification")
def handle_error_notification(data):
    utc_now = datetime.now(pytz.utc)
    ist_timezone = pytz.timezone('Asia/Kolkata')
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
                new_timeSpent
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
            update_query["calls_share"] = new_calls_share
        if new_status:
            update_query["status"] = new_status
        if new_languages:
            update_query["languages"] = new_languages
        if new_score:
            update_query["score"] = new_score
        if new_repeat_score:
            update_query["repeat_score"] = new_repeat_score
        if new_total_score:
            update_query["total_score"] = new_total_score
        if new_categories_names:
            new_categories_object_ids = []
            for category_name in new_categories_names:
                category = categories_collection.find_one({"name": category_name})
                if category:
                    new_categories_object_ids.append(category["_id"])
            update_query["categories"] = new_categories_object_ids
        if new_opening:
            update_query["openingGreeting"] = new_opening
        if new_closing:
            update_query["closingGreeting"] = new_closing
        if new_flow:
            update_query["flow"] = new_flow
        if new_tonality:
            update_query["tonality"] = new_tonality
        if new_timeSplit:
            update_query["timeSplit"] = new_timeSplit
        if new_timeSpent:
            update_query["timeSpent"] = new_timeSpent
        if new_sentiment:
            update_query["userSentiment"] = new_sentiment
        if new_probability:
            update_query["probability"] = new_probability
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
