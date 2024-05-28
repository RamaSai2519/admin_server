import pytz
import requests
import firebase_admin
from bson.objectid import ObjectId
from firebase_admin import credentials
from datetime import datetime, timedelta
from pymongo import MongoClient, DESCENDING

# Firebase initialization
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# MongoDB connection
client = MongoClient(
    "mongodb+srv://sukoon_user:Tcks8x7wblpLL9OA@cluster0.o7vywoz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
# client = MongoClient(
#     "mongodb+srv://techcouncil:2lfNFMZIjdfZJl2R@cluster0.h3kssoa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# )
db = client["test"]
meta_collection = db["meta"]
calls_collection = db["calls"]
users_collection = db["users"]
logs_collection = db["errorlogs"]
experts_collection = db["experts"]
schedules_collection = db["schedules"]
fcm_tokens_collection = db["fcm_tokens"]
categories_collection = db["categories"]
statuslogs_collection = db["statuslogs"]
deleted_users_collection = db["deletedusers"]
applications_collection = db["becomesaarthis"]
deleted_experts_collection = db["deletedexperts"]
deleted_schedules_collection = db["deletedschedules"]

# Ensure indexes
calls_collection.create_index([("initiatedTime", DESCENDING)])
users_collection.create_index([("createdDate", DESCENDING)])
experts_collection.create_index([("createdDate", DESCENDING)])
experts_collection.create_index([("status", 1)])


def updateProfile_status(user):
    if "name" and "phoneNumber" and "city" and "birthDate" in user:
        if "name" != "" and "phoneNumber" != "" and "city" != "" and "birthDate" != "":
            users_collection.update_one(
                {"phoneNumber": user["phoneNumber"]},
                {"$set": {"profileCompleted": True}},
            )


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


def cancel_final_call(record):
    url = "http://localhost:7000/api/v1/cancelJob"
    payload = {"recordIds": [record]}
    requests.delete(url, json=payload)


def cancel_job(record, level):
    url = "http://localhost:7000/api/v1/cancelJob"
    record_ids = [f"{record}-{i}" for i in range(3) if i != level]
    payload = {"recordIds": record_ids}
    requests.post(url, json=payload)


def final_call_job(
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
    requests.post(url, json=payload)


def schedule_job(
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
        "link": f"https://admin-sukoon.vercel.app/approve/{record}",
        "recordId": record,
        "saarthiNumber": expert_number,
        "adminNumber": "9398036558",
        "superAdminNumber": "9398036558",
    }
    requests.post(url, json=payload)


def get_total_duration_in_seconds(time_str):
    hours, minutes, seconds = map(int, time_str.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def get_total_successful_calls_and_duration():
    successful_calls_data = get_calls(
        {"status": "successfull", "duration": {"$exists": True}}
    )
    total_seconds = [
        get_total_duration_in_seconds(call.get("duration", "00:00:00"))
        for call in successful_calls_data
        if get_total_duration_in_seconds(call.get("duration", "00:00:00")) > 60
    ]
    return len(total_seconds), sum(total_seconds)


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
    try:
        hours, minutes, seconds = map(int, duration_str.split(":"))
        return 0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60
    except ValueError:
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
    if user_id not in users_cache:
        user = users_collection.find_one({"_id": user_id}, {"name": 1})
        users_cache[user_id] = user["name"] if user and user.get("name") else "Unknown"
    return users_cache[user_id]


def get_expert_name(expert_id):
    if expert_id not in experts_cache:
        expert = experts_collection.find_one({"_id": expert_id}, {"name": 1})
        experts_cache[expert_id] = (
            expert["name"] if expert and expert.get("name") else "Unknown"
        )
    return experts_cache[expert_id]


def format_duration(duration_in_seconds):
    hours = duration_in_seconds // 3600
    minutes = (duration_in_seconds % 3600) // 60
    seconds = duration_in_seconds % 60

    formatted_duration = []
    if hours > 0:
        formatted_duration.append(f"{hours} h")

    if seconds >= 30:
        formatted_duration.append(f"{minutes + 1} m")
    elif seconds > 0 and minutes > 0:
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
    if response.status_code != 200:
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
        "isBusy": expert.get("isBusy", False),
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


def callUser(expertId, userId):
    url = "http://localhost:5020/api/call/make-call"
    userId = str(userId)
    payload = {"expertId": expertId, "userId": userId}
    response = requests.post(url, json=payload)
    return response.json()


def checkValidity(call):
    initiated_time = call["initiatedTime"]
    if isinstance(initiated_time, str):
        initiated_time = datetime.strptime(initiated_time, "%Y-%m-%d %H:%M:%S.%f")

    utc_zone = pytz.utc
    ist_zone = pytz.timezone("Asia/Kolkata")
    initiated_time = initiated_time.replace(tzinfo=utc_zone).astimezone(ist_zone)
    current_time = datetime.now(ist_zone)

    try:
        if call["duration"] != "":
            duration = get_total_duration_in_seconds(call["duration"])
            duration_timedelta = timedelta(seconds=duration)
            end_time = initiated_time + duration_timedelta
            time_difference = current_time - end_time
        else:
            time_difference = current_time - initiated_time

        if time_difference.total_seconds() <= 600:
            return True
        else:
            hours, remainder = divmod(time_difference.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            return f"The call is {int(hours)} hours and {int(minutes)} minutes old and can't be reconnected."
    except Exception as e:
        return f"Error: {e}"


def get_latest_call(id):
    id = ObjectId(id)
    call = calls_collection.find_one(
        {"$or": [{"_id": id}, {"expert": id}, {"user": id}]},
        sort=[("initiatedTime", DESCENDING)],
    )
    return call


def get_user_context(user_id):
    if meta_collection.find_one({"user": user_id}) is None:
        return "User context not found."
    else:
        try:
            document = meta_collection.find_one({"user": user_id})
            if "context" in document and document["context"] != "":
                context = str(document["context"])
                context = context.split("\n")
                if users_collection.find_one({"_id": user_id}) is not None:
                    user = users_collection.find_one({"_id": user_id})
                    user_city = user["city"]
                    user_dob = user["birthDate"]
                    user_name = user["name"]
                    user_age = datetime.now().year - user_dob.year
                    context.insert(0, f"City: {user_city}")
                    context.insert(0, f"Age: {user_age}")
                    context.insert(0, f"Name: {user_name}")
                return context
            else:
                return "User context not found."
        except Exception as e:
            print(e)
            return "User context not found."


def determine_user_repeation(user_id, expert_id):
    if len(list(calls_collection.find({"user": user_id}))) > 1:
        if len(list(calls_collection.find({"user": user_id, "expert": expert_id}))) > 1:
            return "You have connected to this user before."
        else:
            calls = list(calls_collection.find({"user": user_id}))
            latest_call = calls[-2]
            last_expert_name = get_expert_name(latest_call["expert"])
            return f"The user has spoken to {last_expert_name} in the last session."
    else:
        return "The user is new to the platform."


def get_expert_remarks(id):
    try:
        documents = list(meta_collection.find({"expert": id}))
        if len(documents) > 0:
            remarks = []
            for document in documents:
                if "remark" in document and document["remark"] != "":
                    remarks.append(document["remark"])
            return remarks
        else:
            return ["No Remarks Found."]
    except Exception as e:
        print(e)
        return ["No Remarks found."]
