from datetime import datetime, timedelta
from firebase_admin import credentials
from pymongo import MongoClient, DESCENDING
import firebase_admin
import requests


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
applications_collection = db["becomesaarthis"]
schedules_collection = db["schedules"]

calls_collection.create_index([("initiatedTime", DESCENDING)])
users_collection.create_index([("createdDate", DESCENDING)])
experts_collection.create_index([("createdDate", DESCENDING)])
experts_collection.create_index([("status", 1)])


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


def cancelFinalCall(record):
    url = "http://localhost:7000/api/v1/cancelJob"
    payload = {"recordIds": [record]}
    requests.delete(url, json=payload)


def cancelJob(record, level):
    url = "http://localhost:7000/api/v1/cancelJob"
    if level == "0":
        payload = {"recordIds": [f"{record}-1", f"{record}-2"]}
    elif level == "1":
        payload = {"recordIds": [f"{record}-0", f"{record}-2"]}
    else:
        payload = {"recordIds": [f"{record}-0", f"{record}-1"]}

    requests.post(url, json=payload)


def FinalCallJob(
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
):
    url = "http://localhost:7000/api/v1/scheduleFinalCall"
    payload = {
        "requestId": record,
        "saarthiId": expert_id,
        "userId": user_id,
        "saarthiNumber": int(expert_number),
        "userNumber": int(user_number),
        "year": year,
        "month": month,
        "date": day,
        "hours": hour,
        "minutes": minute,
    }
    print(payload)
    requests.post(url, json=payload)


def scheduleJob(
    expert_name, user_name, year, month, day, hour, minute, expert_number, record
):
    url = "http://localhost:7000/api/v1/scheduleJob"
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
    requests.post(url, json=payload)


def get_total_duration_in_seconds(time_str):
    hours, minutes, seconds = map(int, time_str.split(":"))
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds


def get_total_successful_calls_and_duration():
    successful_calls_data = get_calls(
        {"status": "successfull", "duration": {"$exists": True}}
    )
    total_seconds = []
    for call in successful_calls_data:
        duration = call.get("duration", "00:00:00")
        seconds = sum(
            int(x) * 60**i for i, x in enumerate(reversed(duration.split(":")))
        )
        if seconds > 60:
            total_seconds.append(seconds)

    total_duration_seconds = sum(total_seconds)
    total_successful_calls = len(total_seconds)
    return total_successful_calls, total_duration_seconds


def get_online_saarthis():
    online_saarthis = experts_collection.find(
        {"status": {"$regex": "online"}}, {"categories": 0}
    )
    return [get_formatted_expert(expert) for expert in online_saarthis]


users_cache = {}
experts_cache = {}
call_threads = {}


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


def format_duration(duration_in_seconds):
    hours = duration_in_seconds // 3600
    minutes = (duration_in_seconds % 3600) // 60
    seconds = duration_in_seconds % 60

    formatted_duration = []
    if hours > 0:
        formatted_duration.append(f"{hours} h")

    if seconds >= 30:
        formatted_duration.append(f"{minutes + 1} m")
    elif seconds > 0:
        if minutes > 0:
            formatted_duration.append(f"{minutes} m")

    return " ".join(formatted_duration)


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


def get_calls(query={}, projection={}):
    admin_ids = [
        user["_id"] for user in users_collection.find({"role": "admin"}, {"_id": 1})
    ]
    calls = list(
        calls_collection.find(
            {
                "user": {"$nin": admin_ids},
                **query,
            },
            {
                "_id": 0,
                "recording_url": 0,
                "Score Breakup": 0,
                "Saarthi Feedback": 0,
                "User Callback": 0,
                "Summary": 0,
                "tonality": 0,
                "timeSplit": 0,
                "Sentiment": 0,
                "Topics": 0,
                "timeSpent": 0,
                "userSentiment": 0,
                "probability": 0,
                "openingGreeting": 0,
                "transcript_url": 0,
                "flow": 0,
                "closingGreeting": 0,
                **projection,
            },
        ).sort([("initiatedTime", 1)])
    )

    calls = [format_call(call) for call in calls]
    return calls
