from Utils.config import schedules_collection, experts_collection
from Utils.Helpers.ScheduleManager import ScheduleManager as sm
from datetime import datetime, timedelta
from bson import ObjectId
import pytz

class Slot:
    def __init__(self, expert_id, utc_date, duration):
        self.expert_id = expert_id
        self.utc_date = utc_date
        self.duration = duration
        self.ist_datetime = self.convert_to_ist()
        self.day_name = self.ist_datetime.strftime("%A")
        self.slots = self.calculate_slots() or []

    def convert_to_ist(self):
        utc_datetime = datetime.strptime(self.utc_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        return utc_datetime + timedelta(hours=5, minutes=30)

    def calculate_slots(self):
        return sm.slots_calculater(self.expert_id, self.day_name, self.duration)

    def to_output_slots(self):
        output_slots = []
        utc_zone = pytz.utc
        ist_timezone = pytz.timezone('Asia/Kolkata')

        for slot in self.slots:
            slot_start_str = slot.split(' - ')[0]
            slot_start_time = datetime.strptime(slot_start_str, "%H:%M").time()
            slot_start_ist = datetime.combine(self.ist_datetime.date(), slot_start_time)
            slot_start_utc = (slot_start_ist - timedelta(hours=5, minutes=30)).replace(tzinfo=utc_zone)
            slot_start_utc_str = slot_start_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            slot_dict = {
                "slot": slot,
                "datetime": slot_start_utc_str,
                "available": slot_start_utc >= datetime.now(utc_zone)
            }
            output_slots.append(slot_dict)
            self.check_availability(slot_dict, slot, ist_timezone)
        
        return output_slots

    def check_availability(self, slot_dict, slot, ist_timezone):
        if slot_dict["available"]:
            expert_schedule = schedules_collection.find_one({
                "expert": ObjectId(self.expert_id),
                "datetime": {
                    "$gte": datetime.combine(self.ist_datetime.date(), datetime.strptime(slot.split(' - ')[0], "%H:%M").time()),
                    "$lt": datetime.combine(self.ist_datetime.date(), datetime.strptime(slot.split(' - ')[0], "%H:%M").time()) + timedelta(minutes=self.duration)
                }
            })

            if expert_schedule:
                scheduled_duration = expert_schedule["duration"] if "duration" in expert_schedule else 60
                if scheduled_duration in [30, 60]:
                    slot_dict["available"] = False
                    if scheduled_duration == 60:
                        next_slot = self.slots[self.slots.index(slot) + 1]
                        self.slots.remove(next_slot)

            utc_datetime = datetime.strptime(slot_dict["datetime"], '%Y-%m-%dT%H:%M:%S.%fZ')
            ist_datetime = utc_datetime.astimezone(ist_timezone)
            ist_hour = ist_datetime.hour

            expert_doc = experts_collection.find_one({"_id": ObjectId(self.expert_id)}, {"type": 1})
            expert_type = expert_doc["type"] if expert_doc else None

            if expert_type and expert_type in ["saarthi", "sarathi"]:
                if not (9 <= ist_hour < 22):
                    slot_dict["available"] = False
            else:
                if not (10 <= ist_hour < 14) or not (16 <= ist_hour < 20):
                    slot_dict["available"] = False