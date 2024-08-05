from Utils.config import timings_collection, times
from datetime import timedelta, datetime
from bson.objectid import ObjectId
import requests
import json


class ScheduleManager:
    @staticmethod
    def scheduleCall(time, expert_id, user_id, recordId):
        url = "https://6x4j0qxbmk.execute-api.ap-south-1.amazonaws.com/main/actions/create_scheduled_job"
        time = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        meta = {"expertId": expert_id,
                "userId": user_id, "scheduledCallId": recordId}
        meta = json.dumps(meta)
        payload = {
            "job_type": "CALL",
            "job_time": time,
            "status": "PENDING",
            "request_meta": meta,
            "action": "CREATE"
        }
        response = requests.request("POST", url, data=json.dumps(payload))
        return response.text

    @staticmethod
    def cancelCall(scheduleId):
        url = "https://6x4j0qxbmk.execute-api.ap-south-1.amazonaws.com/main/actions/create_scheduled_job"
        payload = {
            "action": "DELETE",
            "scheduled_job_id": scheduleId
        }
        response = requests.request("POST", url, data=json.dumps(payload))
        return response.text

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
