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
categories_collection = db["categories"]
statuslogs_collection = db["statuslogs"]

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
        pass
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
    formatted_calls = [format_call(call) for call in calls]
    return jsonify(formatted_calls)


@app.route("/api/successful-calls")
def get_successful_calls():
    calls = get_calls({"user": {"$nin": excluded_users}, "status": "successfull"})
    filtered_calls = []
    for call in calls:
        duration_str = call.get("transferDuration", "")
        if is_valid_duration(duration_str) and get_timedelta(duration_str) > timedelta(
            minutes=1
        ):
            filtered_calls.append(format_call(call))
    return jsonify(filtered_calls)


@app.route("/api/users")
def get_users():
    users = list(users_collection.find({"_id": {"$nin": excluded_users}}))
    for user in users:
        user["_id"] = str(user.get("_id", ""))
    return jsonify(users)


@app.route("/api/calls/<string:id>")
def get_call(id):
    call = calls_collection.find_one({"callId": id})
    if not call:
        return jsonify({"error": "Call not found"}), 404

    call["ConversationScore"] = call.pop("Conversation Score", 0)
    formatted_call = format_call(call)
    return jsonify(formatted_call)


@app.route("/api/calls/<string:id>", methods=["PUT"])
def update_call(id):
    data = request.get_json()
    new_conversation_score = data.get("ConversationScore")
    result = calls_collection.update_one(
        {"callId": id}, {"$set": {"Conversation Score": new_conversation_score}}
    )

    if result.modified_count == 0:
        return jsonify({"error": "Failed to update Conversation Score"}), 400
    else:
        return jsonify(new_conversation_score), 200


@app.route("/api/last-five-calls")
def get_last_five_calls():
    try:
        ist = timezone("Asia/Kolkata")
        current_date = datetime.now(ist).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
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
        for call in current_day_calls:
            call["ConversationScore"] = call.pop("Conversation Score", 0)

        if len(current_day_calls) == 0:
            last_five_calls = list(
                calls_collection.find().sort([("initiatedTime", -1)]).limit(5)
            )
            for call in current_day_calls:
                call["ConversationScore"] = call.pop("Conversation Score", 0)
        else:
            last_five_calls = current_day_calls

        formatted_calls = [format_call(call) for call in last_five_calls]
        return jsonify(formatted_calls)
    except Exception as e:
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
        call["ConversationScore"] = call.pop("Conversation Score", 0)

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


@app.route("/api/users/<string:id>", methods=["GET"])
def get_user(id):
    user = users_collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@app.route("/api/users/<string:id>", methods=["PUT"])
def update_user(id):
    user_data = request.json
    new_name = user_data.get("name")
    new_phone_number = user_data.get("phoneNumber")
    new_city = user_data.get("city")
    new_birth_date = user_data.get("birthDate")
    new_number_of_calls = user_data.get("numberOfCalls")

    # Check if any field is provided for update
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
        update_query["birthDate"] = new_birth_date
    if new_number_of_calls:
        update_query["numberOfCalls"] = new_number_of_calls

    result = users_collection.update_one({"_id": ObjectId(id)}, {"$set": update_query})

    if result.modified_count == 0:
        return jsonify({"error": "User not found"}), 404

    updated_user = users_collection.find_one({"_id": ObjectId(id)}, {"_id": 0})
    return jsonify(updated_user)


@app.route("/api/experts/<string:id>", methods=["GET"])
def get_expert(id):
    expert = experts_collection.find_one({"_id": ObjectId(id)})
    if not expert:
        return jsonify({"error": "Expert not found"}), 404
    expert["_id"] = str(expert.get("_id", ""))
    category_names = []
    for category_id in expert.get("categories", []):
        category = categories_collection.find_one({"_id": ObjectId(category_id)})
        if category:
            category_names.append(category.get("name", ""))

    # Update expert document to include category names
    expert["categories"] = category_names
    return jsonify(expert)


@app.route("/api/categories")
def get_categories():
    categories = list(categories_collection.find({}, {"_id": 0, "name": 1}))
    category_names = [category["name"] for category in categories]
    return jsonify(category_names)


@app.route("/api/experts/<string:id>", methods=["PUT"])
def update_expert(id):
    expert_data = request.json

    new_name = expert_data.get("name")
    new_phone_number = expert_data.get("phoneNumber")
    new_topics = expert_data.get("topics")
    new_description = expert_data.get("description")
    new_profile = expert_data.get("profile")
    new_languages = expert_data.get("languages")
    new_score = expert_data.get("score")
    new_repeat_score = expert_data.get("repeat_score")
    new_total_score = expert_data.get("total_score")
    new_categories_names = expert_data.get("categories")

    if not any(
        [
            new_name,
            new_phone_number,
            new_topics,
            new_description,
            new_profile,
            new_languages,
            new_score,
            new_repeat_score,
            new_total_score,
            new_categories_names,
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

        update_query["categories"] = (
            new_categories_object_ids  # Update with new ObjectIds
        )

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

    # Update expert document to include category names
    updated_expert["categories"] = category_names
    return jsonify(updated_expert)


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


from datetime import datetime
from bson import ObjectId


@app.route("/api/experts")
def get_experts():
    experts = list(experts_collection.find({}, {"categories": 0}))
    formatted_experts = []

    for expert in experts:
        expert_id = str(expert["_id"])
        login_logs = list(
            statuslogs_collection.find(
                {"expert": ObjectId(expert_id), "status": "online"}
            )
        )

        # Calculate logged-in hours
        logged_in_hours = calculate_logged_in_hours(login_logs)

        formatted_expert = {
            "_id": expert_id,
            "name": expert.get("name", "Unknown"),
            "phoneNumber": expert.get("phoneNumber", ""),
            "score": expert.get("score", 0),
            "status": expert.get("status", "offline"),
            "loggedInHours": logged_in_hours,
        }
        formatted_experts.append(formatted_expert)

    return jsonify(formatted_experts)


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
    socketio.run(app, host="0.0.0.0", port=80, debug=True, allow_unsafe_werkzeug=True)
