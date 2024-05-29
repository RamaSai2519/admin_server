from Utils.config import users_collection, experts_collection, experts_cache, users_cache
from datetime import timedelta
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
            formatted_duration.append(f"{hours} h")

        if seconds >= 30:
            formatted_duration.append(f"{minutes + 1} m")
        elif seconds > 0 and minutes > 0:
            formatted_duration.append(f"{minutes} m")

        return " ".join(formatted_duration)

    @staticmethod
    def send_push_notification(token, message):
        fcm_url = "https://fcm.googleapis.com/fcm/send"
        server_key = "AAAAM5jkbNg:APA91bG80zQ8CzD1AeQmV45YT4yWuwSgJ5VwvyLrNynAJBk4AcyCb6vbCSGlIQeQFPAndS0TbXrgEL8HFYQq4DMXmSoJ4ek7nFcCwOEDq3Oi5Or_SibSpywYFrnolM4LSxpRkVeiYGDv"
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
            expert = experts_collection.find_one({"_id": expert_id}, {"name": 1})
            experts_cache[expert_id] = (
                expert["name"] if expert and expert["name"] else "Unknown"
            )
        return experts_cache[expert_id]

    @staticmethod
    def get_user_name(user_id):
        if user_id not in users_cache:
            user = users_collection.find_one({"_id": user_id}, {"name": 1})
            users_cache[user_id] = user["name"] if user and user["name"] else "Unknown"
        return users_cache[user_id]
