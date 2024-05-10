from pymongo import MongoClient
from datetime import datetime, timedelta
import requests
import time
import pytz

client = MongoClient(
    "mongodb+srv://sukoon_user:Tcks8x7wblpLL9OA@cluster0.o7vywoz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
db = client["test"]
experts_collection = db["experts"]
fcm_tokens_collection = db["fcm_tokens"]


def send_push_notification(message):
    fcm_url = "https://fcm.googleapis.com/fcm/send"
    server_key = "AAAAM5jkbNg:APA91bG80zQ8CzD1AeQmV45YT4yWuwSgJ5VwvyLrNynAJBk4AcyCb6vbCSGlIQeQFPAndS0TbXrgEL8HFYQq4DMXmSoJ4ek7nFcCwOEDq3Oi5Or_SibSpywYFrnolM4LSxpRkVeiYGDv"
    tokens = list(fcm_tokens_collection.find())
    for token in tokens:
        payload = {
            "to": token["token"],
            "notification": {"title": "Notification", "body": message},
        }
        headers = {
            "Authorization": "key=" + server_key,
            "Content-Type": "application/json",
        }
        response = requests.post(fcm_url, json=payload, headers=headers)
    if response.status_code == 200:
        pass
    else:
        print("Failed to send notification:", response.text)


def job():
    query = {"status": "online"}
    update = {"$set": {"status": "offline"}}
    result = experts_collection.update_many(query, update)
    if result.modified_count > 0:
        send_push_notification("All Saarthis are offline now.")


def run_script():
    while True:
        current_time = datetime.now(pytz.timezone("Asia/Kolkata"))
        if current_time.hour == 21 and current_time.minute == 0:
            job()
            time.sleep(3600)
        else:
            next_hour = (current_time + timedelta(hours=1)).replace(
                minute=0, second=0, microsecond=0
            )
            sleep_duration = (next_hour - current_time).total_seconds()
            time.sleep(sleep_duration)


run_script()
