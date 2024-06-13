"""
Routes from the admin server
 - All the routes are prefixed with /admin
    - The routes are divided into 7 services
        - AuthService
        - AppService
        - CallService
        - DataService
        - UserService
        - ExpertService
        - EventService
    - Each service has its own routes
        - AuthService
            - /admin/auth/login (tested)
            - /admin/auth/refresh (tested)
            - /admin/auth/register (tested)
        - AppService
            - /admin/service/schedule/<string:id> (tested)
            - /admin/service/approve/<string:id>/<level> (tested)
            - /admin/service/save-fcm-token (tested)
            - /admin/service/dashboardstats (tested) (too long)
                Total Time: 850s
                All Calls: 150ms
                Successful Calls: 200ms
                Failed Calls: 150ms
                Missed Calls: 125ms
                Duration: 130ms
                Scheduled Calls: 200ms
                Avg. Score: 200ms
                Online Saarthis: 140ms
        - CallService
            - /admin/call/calls/<string:id> (tested)
            - /admin/call/callUser (tested)
            - /admin/call/connect (tested)
        - DataService
            - /admin/data/errorlogs (tested)
            - /admin/data/calls (tested) 
                (On Server Start: 5.16s) (Later: 228ms)
            - /admin/data/applications (tested)
            - /admin/data/users (tested) 
            - /admin/data/experts (tested)
            - /admin/data/categories (tested)
            - /admin/data/schedules (tested) 
                (On Server Start: 2.49s) (Later: 56ms)
        - UserService
            - /admin/user/leads (tested)
            - /admin/user/users/<string:id> (tested)
        - ExpertService
            - /admin/expert/experts/<string:id> (tested)
            - /admin/expert/popupData/<string:expertId> (tested)
        - EventService
            - /admin/event/events (tested)
            - /admin/event/event (tested)
            - /admin/event/users (tested)
 - A total of 24 routes are present in the admin server @ 07/06/2024
"""

from Utils.Helpers.InsightsManager import InsightsManager
from flask_jwt_extended import JWTManager, jwt_required
from Utils.Services.ExpertService import ExpertService
from Utils.Services.EventService import EventService
from Utils.Services.AuthService import AuthService
from Utils.Services.DataService import DataService
from Utils.Services.CallService import CallService
from Utils.Services.UserService import UserService
from Utils.Services.AppService import AppService
from Utils.config import JWT_SECRET_KEY
from datetime import timedelta
from flask_cors import CORS
from flask import Flask

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(weeks=1)
jwt = JWTManager(app)


# Authentication Route
@app.route("/admin/auth/login", methods=["POST"])
def login_route():
    return AuthService.login()


# Refresh Token Route
@app.route("/admin/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_route():
    return AuthService.refresh()


@app.route("/admin/auth/register", methods=["POST"])
def register_route():
    return AuthService.register()


# Below are the functional routes, prefixed with /service
@app.route("/admin/service/schedule/<id>", methods=["PUT", "DELETE", "GET"])
@jwt_required()
def update_schedule_route(id):
    return AppService.update_schedule(id)


@app.route("/admin/service/approve/<string:id>/<level>", methods=["PUT"])
@jwt_required()
def approve_user(id, level):
    return AppService.approve_application(id, level)


@app.route("/admin/service/save-fcm-token", methods=["POST"])
@jwt_required()
def save_fcm_token_route():
    return AppService.save_fcm_token()


@app.route("/admin/service/dashboardstats")
@jwt_required()
def get_dashboard_stats_route():
    return InsightsManager.get_dashboard_stats()


@app.route("/admin/service/callinsights")
@jwt_required()
def get_call_insights_route():
    return AppService.get_insights()


# Below are the CallService routes, prefixed with /call
@app.route("/admin/call/calls/<string:id>", methods=["GET", "PUT"])
@jwt_required()
def handle_call_route(id):
    return CallService.handle_call(id)


@app.route("/admin/call/callUser", methods=["POST"])
def expert_call_user_route():
    return CallService.expert_call_user()


@app.route("/admin/call/connect", methods=["POST"])
@jwt_required()
def connect_route():
    return CallService.connect()


# Below are the DataService routes, prefixed with /data
@app.route("/admin/data/errorlogs")
@jwt_required()
def get_error_logs_route():
    return DataService.get_error_logs()


@app.route("/admin/data/calls")
@jwt_required()
def get_calls_route():
    return DataService.get_all_calls()


@app.route("/admin/data/applications")
@jwt_required()
def get_applications_route():
    return DataService.get_applications()


@app.route("/admin/data/users")
@jwt_required()
def get_users_route():
    return DataService.get_users()


@app.route("/admin/data/experts")
@jwt_required()
def get_experts_route():
    return DataService.get_experts()


@app.route("/admin/data/categories", methods=["GET", "POST"])
@jwt_required()
def get_categories_route():
    return DataService.get_categories()


@app.route("/admin/data/schedules", methods=["POST", "GET"])
@jwt_required()
def schedules_route():
    return DataService.schedules()


# Below are the ExpertService routes, prefixed with /expert
@app.route("/admin/expert/experts/<string:id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_expert_route(id):
    return ExpertService.handle_expert(id)


@app.route("/admin/expert/create", methods=["POST"])
@jwt_required()
def create_expert_route():
    return ExpertService.create_expert()


@app.route("/admin/expert/popupData/<string:expertId>", methods=["GET"])
def get_popup_data_route(expertId):
    return ExpertService.get_popup_data(expertId)


# Below are the UserService routes, prefixed with /user
@app.route("/admin/user/leads", methods=["GET", "POST"])
@jwt_required()
def get_leads_route():
    return UserService.get_leads()


@app.route("/admin/user/leadRemarks", methods=["POST"])
@jwt_required()
def add_lead_remarks_route():
    return UserService.add_lead_remarks()


@app.route("/admin/user/users/<string:id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_user_route(id):
    return UserService.handle_user(id)


@app.route("/admin/user/engagementData", methods=["GET", "POST", "DELETE"])
@jwt_required()
def get_online_users_route():
    return UserService.get_engagement_data()


# Below are the EventService routes, prefixed with /event
@app.route("/admin/event/events", methods=["GET"])
@jwt_required()
def get_events_route():
    return EventService.get_events()


@app.route("/admin/event/event", methods=["GET", "PUT", "POST"])
@jwt_required()
def get_event_route():
    return EventService.get_event()


@app.route("/admin/event/users", methods=["GET"])
@jwt_required()
def get_users_by_event_route():
    return EventService.get_users_by_event()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        # debug=True,
    )
