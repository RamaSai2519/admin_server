from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from concurrent.futures import ThreadPoolExecutor, as_completed
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.ExpertManager import ExpertManager as em
from Utils.Helpers.CallManager import CallManager as cm
from Utils.config import users_collection
from datetime import datetime
from flask import jsonify
import pytz


class ExecutionManager:
    @staticmethod
    def get_dashboard_stats():
        # Get today's date and time
        current_date = datetime.now(pytz.timezone("Asia/Kolkata"))
        today_start = datetime.combine(current_date, datetime.min.time())
        today_end = datetime.combine(current_date, datetime.max.time())
        today_calls_query = {"initiatedTime": {"$gte": today_start, "$lt": today_end}}

        total_successful_calls, total_duration_seconds = (
            cm.get_total_successful_calls_and_duration()
        )

        # Define functions for each calculation
        def totalCalls():
            return uf.get_calls_count()

        def todayCalls():
            return uf.get_calls_count(today_calls_query)

        def successfulCalls():
            return uf.get_calls_count({"status": "successfull", "failedReason": ""})

        def todaySuccessfulCalls():
            return uf.get_calls_count(
                {"status": "successfull", "failedReason": "", **today_calls_query}
            )

        def failedCalls():
            return uf.get_calls_count({"status": "failed"})

        def todayFailedCalls():
            today_failed_calls_query = {"status": "failed", **today_calls_query}
            return uf.get_calls_count(today_failed_calls_query)

        def missedCalls():
            missed_calls_query = {"failedReason": "call missed"}
            return uf.get_calls_count(missed_calls_query)

        def todayMissedCalls():
            today_missed_calls_query = {
                "failedReason": "call missed",
                **today_calls_query,
            }
            return uf.get_calls_count(today_missed_calls_query)

        def totalDuration():
            return hf.format_duration(cm.get_total_duration())

        def averageCallDuration():
            average_call_duration = (
                hf.format_duration(total_duration_seconds / total_successful_calls)
                if total_successful_calls
                else "0 minutes"
            )
            return average_call_duration

        def scheduledCallsPercentage():
            successful_scheduled_calls = cm.get_successful_scheduled_calls()
            scheduled_calls_percentage = round(
                (
                    successful_scheduled_calls / total_successful_calls * 100
                    if total_successful_calls
                    else 0
                ),
                2,
            )
            return scheduled_calls_percentage

        def averageConversationScore():
            return cm.calculate_average_conversation_score()

        def onlineSaarthis():
            return em.get_online_saarthis()

        # Use ThreadPoolExecutor to run calculations concurrently
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(fn): fn.__name__
                for fn in [
                    totalCalls,
                    todayCalls,
                    successfulCalls,
                    todaySuccessfulCalls,
                    failedCalls,
                    todayFailedCalls,
                    missedCalls,
                    todayMissedCalls,
                    totalDuration,
                    averageCallDuration,
                    scheduledCallsPercentage,
                    averageConversationScore,
                    onlineSaarthis,
                ]
            }

            stats_data = {}
            for future in as_completed(futures):
                key = futures[future]
                stats_data[key] = future.result()

        return jsonify(stats_data)

    @staticmethod
    def get_call_insights():
        successful_calls = uf.get_calls(
            {"status": "successfull", "failedReason": ""}, {"duration": 1}, False, False
        )
        users = list(
            users_collection.find(
                {"role": {"$ne": "admin"}, "name": {"$exists": True}},
                {"Customer Persona": 0},
            )
        )
        for user in users:
            calls = uf.get_calls({"user": user["_id"]}, {"duration": 1}, False, False)
            if calls:
                if calls == 1:
                    user["type"] = "first call active"
                elif calls == 2:
                    user["type"] = "second call active"
                else:
                    user["type"] = "active"
                    

        def lt_15_min():
            return len([call for call in successful_calls if call["duration"] < 900])

        def gt_15_min_lt_30_min():
            return len(
                [call for call in successful_calls if 900 <= call["duration"] < 1800]
            )

        def gt_30_min_lt_45_min():
            return len(
                [call for call in successful_calls if 1800 <= call["duration"] < 2700]
            )

        def gt_45_min_lt_60_min():
            return len(
                [call for call in successful_calls if 2700 <= call["duration"] < 3600]
            )

        def gt_60_min():
            return len([call for call in successful_calls if call["duration"] >= 3600])
