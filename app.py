"""
Routes from the admin server
 - All the routes are prefixed with /admin
    - The routes are divided into 5 services
        - AppService
        - CallService
        - DataService
        - UserService
        - ExpertService
    - Each service has its own routes
        - AuthService
            - /admin/auth/login (tested)
            - /admin/auth/refresh (tested)
            - /admin/auth/register (tested)
        - AppService
            - /admin/service/schedule/<string:id> (tested)
            - /admin/service/approve/<string:id>/<level> (tested)
            - /admin/service/save-fcm-token (tested)
            - /admin/service/dashboardstats (tested) (too long) (data)
        - CallService
            - /admin/call/calls/<string:id> (tested)
            - /admin/call/callUser (tested)
            - /admin/call/connect (tested)
        - DataService
            - /admin/data/errorlogs (tested)
            - /admin/data/calls (tested) (too long)
            - /admin/data/applications (tested)
            - /admin/data/users (tested) (Will take long in future)
            - /admin/data/experts (tested)
            - /admin/data/categories (tested)
            - /admin/data/schedules (tested) (too long)
        - UserService
            - /admin/user/leads (tested)
            - /admin/user/users/<string:id> (tested)
        - ExpertService
            - /admin/expert/experts/<string:id> (tested)
            - /admin/expert/popupData/<string:expertId> (tested)
 - A total of 20 routes are present in the admin server @ 30/05/2024
"""

from flask_jwt_extended import JWTManager, jwt_required
from Utils.Services.ExpertService import ExpertService
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
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=1)
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
    return AppService.get_dashboard_stats()


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


@app.route("/admin/data/categories")
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


@app.route("/admin/expert/popupData/<string:expertId>", methods=["GET"])
def get_popup_data_route(expertId):
    return ExpertService.get_popup_data(expertId)


# Below are the UserService routes, prefixed with /user
@app.route("/admin/user/leads", methods=["GET"])
@jwt_required()
def get_leads_route():
    return UserService.get_leads()


@app.route("/admin/user/users/<string:id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_user_route(id):
    return UserService.handle_user(id)


if __name__ == "__main__":
    app.run(port=8080)
    