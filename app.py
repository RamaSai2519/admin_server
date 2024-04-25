from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime, timedelta
from excluded_users import excluded_users
from pytz import timezone
import requests
import firebase_admin
from firebase_admin import credentials

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Firebase Admin SDK with service account credentials
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Connect to MongoDB
client = MongoClient(
    "mongodb+srv://sukoon_user:Tcks8x7wblpLL9OA@cluster0.o7vywoz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["test"]
blogs_collection = db["blogposts"]
calls_collection = db["calls"]
experts_collection = db["experts"]
users_collection = db["users"]
fcm_tokens_collection = db["fcm_tokens"]
logs_collection = db["errorlogs"]

users_cache = {}
experts_cache = {}


def send_push_notification(token, message):
    fcm_url = "https://fcm.googleapis.com/fcm/send"
    server_key = "AAAAM5jkbNg:APA91bG80zQ8CzD1AeQmV45YT4yWuwSgJ5VwvyLrNynAJBk4AcyCb6vbCSGlIQeQFPAndS0TbXrgEL8HFYQq4DMXmSoJ4ek7nFcCwOEDq3Oi5Or_SibSpywYFrnolM4LSxpRkVeiYGDv"

    payload = {
        "to": token,
        "notification": {"title": "Error Notification", "body": message},
    }

    headers = {"Authorization": "key=" + server_key, "Content-Type": "application/json"}

    response = requests.post(fcm_url, json=payload, headers=headers)

    if response.status_code == 200:
        print("Notification sent successfully")
    else:
        print("Failed to send notification:", response.text)


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


def format_call(call):
    user_id = call.get("user", "Unknown")
    expert_id = call.get("expert", "Unknown")
    call["_id"] = str(call.get("_id", ""))
    call["userName"] = get_user_name(user_id)
    call["user"] = str(user_id)
    call["expertName"] = get_expert_name(expert_id)
    call["expert"] = str(expert_id)
    return call


def get_calls(query={}, fields={"_id": 0}):
    calls = list(calls_collection.find(query, fields).sort([("initiatedTime", 1)]))
    return calls


@socketio.on("error_notification")
def handle_error_notification(data):
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    document = {"message": data, "time": time}

    for key, value in document.items():
        if isinstance(value, ObjectId):
            document[key] = str(value)

    logs_collection.insert_one(document)
    print(document)
    emit("error_notification", document, broadcast=True)
    tokens = list(fcm_tokens_collection.find())
    for token in tokens:
        token["_id"] = str(token.get("_id", ""))
        send_push_notification(token["token"], data)


@app.route("/api/save-fcm-token", methods=["POST"])
def save_fcm_token():
    data = request.json
    token = data.get("token")
    if token:
        fcm_tokens_collection.insert_one({"token": token})
        return jsonify({"message": "FCM token saved successfully"}), 200
    else:
        return jsonify({"error": "FCM token missing"}), 400


@app.route("/api/errorlogs")
def get_error_logs():
    error_logs = list(logs_collection.find())
    print(error_logs)
    for log in error_logs:
        log["_id"] = str(log.get("_id", ""))
    print(error_logs)
    return jsonify(error_logs)


@app.route("/api/calls")
def get_calls_route():
    calls = get_calls({"user": {"$nin": excluded_users}})
    formatted_calls = [format_call(call) for call in calls]
    return jsonify(formatted_calls)


@app.route("/api/successful-calls")
def get_successful_calls():
    calls = get_calls({"user": {"$nin": excluded_users}, "status": "successfull"})
    filtered_calls = []
    for call in calls:
        duration_str = call.get("transferDuration", "")
        if is_valid_duration(duration_str) and get_timedelta(duration_str) > timedelta(
            minutes=2
        ):
            filtered_calls.append(format_call(call))
    return jsonify(filtered_calls)


@app.route("/api/users")
def get_users():
    users = list(users_collection.find({"_id": {"$nin": excluded_users}}))
    for user in users:
        user["_id"] = str(user.get("_id", ""))
    return jsonify(users)


@app.route("/api/experts")
def get_experts():
    experts = experts_collection.find({}, {"categories": 0})
    formatted_experts = [
        {"_id": str(expert["_id"]), "name": expert.get("name", "Unknown")}
        for expert in experts
    ]
    return jsonify(formatted_experts)


@app.route("/api/calls/<string:id>")
def get_call(id):
    call = calls_collection.find_one({"callId": id})
    if not call:
        return jsonify({"error": "Call not found"}), 404

    formatted_call = format_call(call)
    return jsonify(formatted_call)


@app.route("/api/last-five-calls")
def get_last_five_calls():
    try:
        ist = timezone("Asia/Kolkata")
        current_date = datetime.now(ist).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        print(current_date)
        current_day_calls = list(
            calls_collection.find(
                {
                    "initiatedTime": {
                        "$gte": current_date,
                        "$lt": current_date + timedelta(days=1),
                    }
                }
            ).sort([("initiatedTime", -1)])
        )

        if len(current_day_calls) == 0:
            last_five_calls = list(
                calls_collection.find().sort([("initiatedTime", -1)]).limit(5)
            )
        else:
            last_five_calls = current_day_calls

        formatted_calls = [format_call(call) for call in last_five_calls]
        return jsonify(formatted_calls)
    except Exception as e:
        print("Error fetching calls:", e)
        return jsonify({"error": "Failed to fetch calls"}), 500


@app.route("/api/all-calls")
def get_all_calls():
    all_calls = get_calls({"user": {"$nin": excluded_users}})
    user_ids = set(call.get("user") for call in all_calls)
    expert_ids = set(call.get("expert") for call in all_calls)

    users = {
        str(user["_id"]): user.get("name", "Unknown")
        for user in users_collection.find({"_id": {"$in": list(user_ids)}}, {"name": 1})
    }
    experts = {
        str(expert["_id"]): expert.get("name", "Unknown")
        for expert in experts_collection.find(
            {"_id": {"$in": list(expert_ids)}}, {"name": 1}
        )
    }

    formatted_calls = []
    for call in all_calls:
        call["userName"] = users.get(str(call.get("user")), "Unknown")
        call["user"] = str(call.get("user", "Unknown"))
        call["expertName"] = experts.get(str(call.get("expert")), "Unknown")
        call["expert"] = str(call.get("expert", "Unknown"))
        call["_id"] = str(call.get("_id", ""))
        formatted_calls.append(call)

    return jsonify(formatted_calls)


@app.route("/api/online-saarthis")
def get_online_saarthis():
    online_saarthis = experts_collection.find({"status": "online"}, {"categories": 0})
    formatted_saarthis = [
        {"_id": str(saarthi["_id"]), "name": saarthi.get("name", "Unknown")}
        for saarthi in online_saarthis
    ]
    return jsonify(formatted_saarthis)


@app.route("/api/users/<string:id>")
def get_user(id):
    user = users_collection.find_one({"_id": ObjectId(id)}, {"name": 1})
    if not user:
        return jsonify({"error": "User not found"}), 404
    user["_id"] = str(user.get("_id", ""))
    return jsonify(user)


@app.route("/api/experts/<string:id>")
def get_expert(id):
    expert = experts_collection.find_one({"_id": ObjectId(id)}, {"categories": 0})
    if not expert:
        return jsonify({"error": "Expert not found"}), 404
    expert["_id"] = str(expert.get("_id", ""))
    return jsonify(expert)


@app.route("/api/blogs")
def get_blogs():
    blogs = list(blogs_collection.find({}, {"_id": 0}))
    return jsonify(blogs)


@app.route("/api/blogs/<string:id>")
def get_blog(id):
    blog = blogs_collection.find_one({"id": id})
    if not blog:
        return jsonify({"error": "Blog not found"}), 404
    blog["_id"] = str(blog["_id"])
    return jsonify(blog)


@app.route("/api/featuredblog")
def get_featured_blog():
    featured_blog = blogs_collection.find_one(sort=[("id", -1)])
    if not featured_blog:
        return jsonify({"error": "Featured blog not found"}), 404
    featured_blog["_id"] = str(featured_blog["_id"])
    return jsonify(featured_blog)


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


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=80, debug=True, allow_unsafe_werkzeug=True)
