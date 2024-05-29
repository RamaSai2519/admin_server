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
