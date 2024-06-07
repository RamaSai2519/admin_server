from Utils.Helpers.UtilityFunctions import UtilityFunctions as uf
from concurrent.futures import ThreadPoolExecutor, as_completed
from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.Helpers.ExpertManager import ExpertManager as em
from Utils.Helpers.CallManager import CallManager as cm
from datetime import datetime
from flask import jsonify
import pytz


class InsightsManager:
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
            successful_scheduled_calls = len(cm.get_successful_scheduled_calls())
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
            {"duration": 1, "user": 1, "type": 1, "_id": 0},
            False,
            False,
        )

        def classify_durations():
            def duration_category(call):
                duration_sec = hf.get_total_duration_in_seconds(call["duration"])
                if duration_sec < 900:
                    return "_15min"
                elif 900 <= duration_sec < 1800:
                    return "_15_30min"
                elif 1800 <= duration_sec < 2700:
                    return "_30_45min"
                elif 2700 <= duration_sec < 3600:
                    return "_45_60min"
                else:
                    return "_60min_"

            duration_counts = {
                "_15min": 0,
                "_15_30min": 0,
                "_30_45min": 0,
                "_45_60min": 0,
                "_60min_": 0,
            }

            for call in successful_calls:
                category = duration_category(call)
                duration_counts[category] += 1

            total_calls = len(successful_calls)
            for key in duration_counts:
                duration_counts[key] = (
                    f"{round((duration_counts[key] / total_calls) * 100, 2)}%"
                )

            return duration_counts

        def average_durations():
            unique_users = set(call["user"] for call in successful_calls)
            calls_by_user = {user: [] for user in unique_users}
            for call in successful_calls:
                calls_by_user[call["user"]].append(call)

            user_types = {}
            for user, user_calls in calls_by_user.items():
                call_count = len(user_calls)
                if call_count == 1:
                    user_type = "one_call"
                elif call_count == 2:
                    user_type = "two_calls"
                else:
                    user_type = "repeat_calls"
                user_types[user] = user_type

            durations_by_type = {}
            for user, user_calls in calls_by_user.items():
                user_type = user_types[user]
                if user_type not in durations_by_type:
                    durations_by_type[user_type] = {"sum": 0, "count": 0}
                for call in user_calls:
                    durations_by_type[user_type][
                        "sum"
                    ] += hf.get_total_duration_in_seconds(call["duration"])
                    durations_by_type[user_type]["count"] += 1

            average_durations = {
                user_type: hf.format_duration(data["sum"] / data["count"])
                for user_type, data in durations_by_type.items()
            }

            scheduled_calls = cm.get_successful_scheduled_calls()
            scheduled_call_durations = [
                hf.get_total_duration_in_seconds(call["duration"])
                for call in scheduled_calls
            ]
            average_scheduled_duration = hf.format_duration(
                sum(scheduled_call_durations) / len(scheduled_call_durations)
                if scheduled_call_durations
                else 0
            )
            average_durations["scheduled_avg_duration"] = average_scheduled_duration

            organic_calls = [
                call
                for call in successful_calls
                if "type" not in call or call["type"] != "scheduled"
            ]
            organic_call_durations = [
                hf.get_total_duration_in_seconds(call["duration"])
                for call in organic_calls
            ]
            average_organic_duration = hf.format_duration(
                sum(organic_call_durations) / len(organic_call_durations)
                if organic_call_durations
                else 0
            )
            average_durations["organic_avg_duration"] = average_organic_duration

            first_calls = durations_by_type["one_call"]["count"]
            second_calls = durations_by_type["two_calls"]["count"]
            repeat_calls = durations_by_type["repeat_calls"]["count"]
            total_calls = first_calls + second_calls + repeat_calls

            first_calls = f"{round((first_calls / total_calls) * 100, 2)}%"
            second_calls = f"{round((second_calls / total_calls) * 100, 2)}%"
            repeat_calls = f"{round((repeat_calls / total_calls) * 100, 2)}%"

            average_durations["first_calls_split"] = first_calls
            average_durations["second_calls_split"] = second_calls
            average_durations["repeat_calls_split"] = repeat_calls

            return average_durations

        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(fn): fn.__name__
                for fn in [classify_durations, average_durations]
            }

            insights_data = {}
            for future in as_completed(futures):
                insights_data.update(future.result())

            """
            This is the final insights_data dictionary:
            {
                "_15min": "52.05%",
                "15_30min": "22.13%",
                "30_45min": "14.96%",
                "45_60min": "6.15%",
                "60min_": "4.71%",
                "first_calls_split": "9.22%",
                "second_calls_split": "11.89%",
                "repeat_calls_split": "78.89%",
                "one_call": "17m 44s",
                "two_calls": "14m 8s"
                "repeat_calls": "20m 39s",
                "organic_avg_duration": "20m 34s",                
                "scheduled_avg_duration": "13m 12s",
            }
            """

        return insights_data
