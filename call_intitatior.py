import requests
from flask import jsonify, request
from pymongo import MongoClient
from bson import ObjectId
import threading
import pytz
from time import sleep
from datetime import datetime

client = MongoClient(
    "mongodb+srv://sukoon_user:Tcks8x7wblpLL9OA@cluster0.o7vywoz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["test"]
experts_collection = db["experts"]
users_collection = db["users"]
schedules_collection = db["schedules"]


def schedule():
    if request.method == "GET":
        schedules = list(schedules_collection.find())
        for schedule in schedules:
            schedule["_id"] = str(schedule.get("_id", ""))
            expert_id = schedule.get("expert", "")
            expert = experts_collection.find_one({"_id": expert_id}, {"name": 1})
            schedule["expert"] = expert.get("name", "") if expert else ""
            user_id = schedule.get("user", "")
            user = users_collection.find_one({"_id": user_id}, {"name": 1})
            schedule["user"] = user.get("name", "") if user else ""
        return jsonify(schedules)
    elif request.method == "POST":
        data = request.json
        expert = data.get("expert")
        user = data.get("user")
        time = data.get("datetime")

        document = {
            "expert": ObjectId(expert),
            "user": ObjectId(user),
            "datetime": time,
        }
        schedules_collection.insert_one(document)

        expert = experts_collection.find_one(
            {"_id": ObjectId(expert)}, {"phoneNumber": 1}
        )
        expert = expert.get("phoneNumber", "")
        user = users_collection.find_one({"_id": ObjectId(user)}, {"phoneNumber": 1})
        user = user.get("phoneNumber", "")
        threading.Thread(
            target=call_at_specified_time,
            args=(time, expert, user),
            name=f"CallThread {expert}",
        ).start()

        return jsonify({"message": "Data received successfully"})
    else:
        return jsonify({"error": "Invalid request method"}), 404


def call_at_specified_time(time, expert, user):
    scheduled_time = datetime.strptime(time, r"%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=pytz.utc
    )
    current_time = datetime.now(pytz.utc)
    delay = scheduled_time - current_time
    if delay.total_seconds() > 0:
        sleep(delay.total_seconds())
        call_intiator(expert, user)


def call_intiator(expert_number, user_number):
    url = "https://kpi.knowlarity.com/Basic/v1/account/call/makecall"
    payload = {
        "k_number": "+918035384523",
        "agent_number": "+91" + expert_number,
        "customer_number": "+91" + user_number,
        "caller_id": "+918035384523",
    }
    headers = {
        "x-api-key": "bb2S4y2cTvaBVswheid7W557PUzUVMnLaPnvyCxI",
        "authorization": "0738be9e-1fe5-4a8b-8923-0fe503e87deb",
    }
    response = requests.post(url, json=payload, headers=headers)

    return response.json()
