from Utils.config import schedules_collection, calls_collection
from datetime import timedelta, datetime
import requests


class ScheduleManager:
    @staticmethod
    def cancel_final_call(record):
        url = "http://localhost:7000/api/v1/cancelJob"
        payload = {"recordIds": [record]}
        requests.delete(url, json=payload)

    @staticmethod
    def cancel_job(record, level):
        url = "http://localhost:7000/api/v1/cancelJob"
        record_ids = [f"{record}-{i}" for i in range(3) if i != level]
        payload = {"recordIds": record_ids}
        requests.post(url, json=payload)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def update_schedule_status():
        schedules = list(schedules_collection.find())

        for schedule in schedules:
            schedule_user = schedule["user"]
            schedule_expert = schedule["expert"]

            # Adjust schedule time to match call time (assuming your schedule time is in UTC and call time is in local time)
            schedule_time = schedule["datetime"] - timedelta(hours=5, minutes=30)

            # Find calls for the same user and expert within a small time window around the schedule time
            calls = list(
                calls_collection.find(
                    {
                        "user": schedule_user,
                        "expert": schedule_expert,
                        "initiatedTime": {
                            "$gte": schedule_time - timedelta(minutes=1),
                            "$lte": schedule_time + timedelta(minutes=1),
                        },
                    }
                )
            )

            if calls:
                schedules_collection.update_one(
                    {"_id": schedule["_id"]}, {"$set": {"status": "completed"}}
                )
                for call in calls:
                    # Update the call type in the database
                    call_type = "scheduled"
                    calls_collection.update_one(
                        {"_id": call["_id"]}, {"$set": {"type": call_type}}
                    )
                    print(
                        f"Updated call type for call initiated at {call['initiatedTime']}"
                    )
            else:
                if schedule_time < datetime.now():
                    schedules_collection.update_one(
                        {"_id": schedule["_id"]}, {"$set": {"status": "missed"}}
                    )
                    print(f"Updated status for missed schedule at {schedule_time}")
                else:
                    schedules_collection.update_one(
                        {"_id": schedule["_id"]}, {"$set": {"status": "pending"}}
                    )
                    print(f"Updated status for pending schedule at {schedule_time}")
