from Utils.config import timings_collection
from datetime import timedelta, datetime
from bson.objectid import ObjectId
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
    def slots_calculater(expert_id, day):
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
            while current_time + timedelta(minutes=30) <= end_time:
                end_slot_time = current_time + timedelta(minutes=30)
                slots.append(f"{current_time.strftime(
                    '%H:%M')} - {end_slot_time.strftime('%H:%M')}")
                current_time = end_slot_time

            return slots

        # Generate slots for primary time
        primary_slots = generate_slots(
            timing['PrimaryStartTime'], timing['PrimaryEndTime'])

        # Generate slots for secondary time, if available
        secondary_slots = []
        if 'SecondaryStartTime' in timing and 'SecondaryEndTime' in timing:
            secondary_slots = generate_slots(
                timing['SecondaryStartTime'], timing['SecondaryEndTime'])

        # Combine primary and secondary slots
        all_slots = primary_slots + secondary_slots

        return all_slots
