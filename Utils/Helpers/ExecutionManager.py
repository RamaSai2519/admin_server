from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from Utils.Helpers.CallManager import CallManager as cm
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.ExpertManager import ExpertManager as em
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pytz
from flask import jsonify


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
