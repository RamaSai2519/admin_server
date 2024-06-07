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
        # Retrieve all necessary data in bulk
        successful_calls = uf.get_calls(
            {"status": "successfull", "failedReason": ""},
            {"duration": 1, "user": 1},
            False,
            False,
        )

        users = list(
            users_collection.find(
                {"role": {"$ne": "admin"}, "name": {"$exists": True}},
                {"_id": 1},
            )
        )

        user_call_counts = {user["_id"]: 0 for user in users}

        # Update user call counts
        for call in successful_calls:
            user_id = call.get("user")
            if user_id in user_call_counts:
                user_call_counts[user_id] += 1

        def classify_users():
            user_types = {
                "inactive": 0,
                "first call active": 0,
                "second call active": 0,
                "active": 0,
            }
            for user in users:
                calls = user_call_counts.get(user["_id"], 0)
                if calls == 1:
                    user_type = "first call active"
                elif calls == 2:
                    user_type = "second call active"
                elif calls > 2:
                    user_type = "active"
                else:
                    user_type = "inactive"
                user_types[user_type] += 1
            return user_types

        def classify_durations():
            def duration_category(call):
                duration_sec = hf.get_total_duration_in_seconds(call["duration"])
                if duration_sec < 900:
                    return "lt_15_min"
                elif 900 <= duration_sec < 1800:
                    return "gt_15_min_lt_30_min"
                elif 1800 <= duration_sec < 2700:
                    return "gt_30_min_lt_45_min"
                elif 2700 <= duration_sec < 3600:
                    return "gt_45_min_lt_60_min"
                else:
                    return "gt_60_min"

            duration_counts = {
                "lt_15_min": 0,
                "gt_15_min_lt_30_min": 0,
                "gt_30_min_lt_45_min": 0,
                "gt_45_min_lt_60_min": 0,
                "gt_60_min": 0,
            }

            for call in successful_calls:
                category = duration_category(call)
                duration_counts[category] += 1

            total_calls = len(successful_calls)
            for key in duration_counts:
                duration_counts[key] = round((duration_counts[key] / total_calls) * 100, 2)

            return duration_counts

        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(fn): fn.__name__
                for fn in [classify_users, classify_durations]
            }

            insights_data = {}
            for future in as_completed(futures):
                insights_data.update(future.result())

        return jsonify(insights_data)
