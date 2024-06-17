from Utils.config import (
    experts_collection,
    users_collection,
    experts_cache,
    users_cache,
    FB_SERVER_KEY,
)
from datetime import timedelta, datetime
import requests


class HelperFunctions:
    @staticmethod
    def get_timedelta(duration_str):
        try:
            hours, minutes, seconds = map(int, duration_str.split(":"))
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        except ValueError:
            return timedelta(seconds=0)

    @staticmethod
    def get_total_duration_in_seconds(time_str):
        hours, minutes, seconds = map(int, time_str.split(":"))
        return hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def is_valid_duration(duration_str):
        try:
            hours, minutes, seconds = map(int, duration_str.split(":"))
            return 0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60
        except ValueError:
            return False

    @staticmethod
    def format_duration(duration_in_seconds):
        hours = duration_in_seconds // 3600
        minutes = (duration_in_seconds % 3600) // 60
        seconds = duration_in_seconds % 60

        formatted_duration = []
        if hours > 0:
            formatted_duration.append(f"{hours}h")

        if minutes > 0:
            minutes = int(minutes)
            formatted_duration.append(f"{minutes}m")

        if seconds > 0:
            seconds = int(seconds)
            formatted_duration.append(f"{seconds}s")

        return " ".join(formatted_duration) if formatted_duration else "0s"

    @staticmethod
    def send_push_notification(token, message):
        fcm_url = "https://fcm.googleapis.com/fcm/send"
        server_key = FB_SERVER_KEY
        payload = {
            "to": token,
            "notification": {"title": "Notification", "body": message},
        }
        headers = {
            "Authorization": "key=" + server_key,
            "Content-Type": "application/json",
        }
        response = requests.post(fcm_url, json=payload, headers=headers)
        if response.status_code != 200:
            print("Failed to send notification:", response.text)

    @staticmethod
    def get_expert_name(expert_id):
        if expert_id not in experts_cache:
            expert = experts_collection.find_one(
                {"_id": expert_id}, {"name": 1})
            experts_cache[expert_id] = (
                expert["name"] if expert and expert["name"] else "Unknown"
            )
        return experts_cache[expert_id]

    @staticmethod
    def get_user_name(user_id):
        if user_id not in users_cache:
            user = users_collection.find_one({"_id": user_id}, {"name": 1})
            users_cache[user_id] = user["name"] if user and "name" in user else "Unknown"
        return users_cache[user_id]

    @staticmethod
    def calculate_logged_in_hours(login_logs):
        total_logged_in_hours = 0
        last_logged_out_time = None

        for log in login_logs:
            if log["status"] == "online":
                logged_in_at = log["date"]
                logged_out_at = (
                    datetime.now()
                    if last_logged_out_time is None
                    else last_logged_out_time
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
