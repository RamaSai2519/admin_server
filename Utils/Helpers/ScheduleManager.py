from Utils.config import timings_collection, times
from datetime import timedelta, datetime
from bson.objectid import ObjectId
import requests
import json


class ScheduleManager:
    @staticmethod
    def scheduleCall(time, expert_id, user_id):
        url = "https://6x4j0qxbmk.execute-api.ap-south-1.amazonaws.com/main/actions/create_scheduled_job"
        time = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        meta = {"expertId": expert_id, "userId": user_id}
        meta = json.dumps(meta)
        payload = {
            "job_type": "CALL",
            "job_time": time,
            "status": "PENDING",
            "request_meta": meta
        }
        response = requests.request("POST", url, data=json.dumps(payload))
        return response.text

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
    def slots_calculater(expert_id, day, duration=30):
        if expert_id is None or expert_id == "":
            print("Expert ID is required")
            return None
        timings = list(timings_collection.find(
            {"expert": ObjectId(expert_id)}))

        # Find the schedule for the specified day
        timing = next(
            (s for s in timings if s['day'].lower() == day.lower()), None)

        if not timing:
            print(f"No schedule found for {day}")
            return

        # Function to generate time slots
        def generate_slots(start_time_str, end_time_str):
            start_time = datetime.strptime(start_time_str, '%H:%M')
            end_time = datetime.strptime(end_time_str, '%H:%M')
            slots = []

            current_time = start_time
            while current_time + timedelta(minutes=duration) <= end_time:
                end_slot_time = current_time + timedelta(minutes=duration)
                slots.append(f"{current_time.strftime(
                    '%H:%M')} - {end_slot_time.strftime('%H:%M')}")
                current_time = end_slot_time

            return slots

        # Generate slots for primary time
        primary_slots = generate_slots(
            timing[times[0]], timing[times[1]]) if times[0] in timing and timing[times[0]] != "" else []

        # Generate slots for secondary time, if available
        secondary_slots = generate_slots(
            timing[times[2]], timing[times[3]]) if times[2] in timing and timing[times[2]] != "" else []

        # Combine primary and secondary slots
        all_slots = primary_slots + secondary_slots

        return all_slots
