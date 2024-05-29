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
        - AppService
            - /admin/service/schedule/<string:id>
            - /admin/service/approve/<string:id>/<level>
            - /admin/service/save-fcm-token
            - /admin/service/dashboardstats
        - CallService
            - /admin/call/calls/<string:id>
            - /admin/call/callUser
            - /admin/call/connect
        - DataService
            - /admin/data/errorlogs
            - /admin/data/calls
            - /admin/data/applications
            - /admin/data/users
            - /admin/data/experts
            - /admin/data/categories
            - /admin/data/schedules
        - UserService
            - /admin/user/leads
            - /admin/user/users/<string:id>
        - ExpertService
            - /admin/expert/experts/<string:id>
            - /admin/expert/popupData/<string:expertId>
 - A total of 17 routes are present in the admin server
"""

from Utils.Services.ExpertService import ExpertService
from Utils.Services.DataService import DataService
from Utils.Services.CallService import CallService
from Utils.Services.UserService import UserService
from Utils.Services.AppService import AppService
from flask_cors import CORS
from flask import Flask

app = Flask(__name__)
CORS(app)


# Below are the functional routes, prefixed with /service
@app.route("/admin/service/schedule/<id>", methods=["PUT", "DELETE", "GET"])
def update_schedule_route(id):
    return AppService.update_schedule(id)


@app.route("/admin/service/approve/<string:id>/<level>", methods=["PUT"])
def approve_user(id, level):
    return AppService.approve_application(id, level)


@app.route("/admin/service/save-fcm-token", methods=["POST"])
def save_fcm_token_route():
    return AppService.save_fcm_token()


@app.route("/admin/service/dashboardstats")
def get_dashboard_stats_route():
    return AppService.get_dashboard_stats()


# Below are the CallService routes, prefixed with /call
@app.route("/admin/call/calls/<string:id>", methods=["GET", "PUT"])
def handle_call_route(id):
    return CallService.handle_call(id)


@app.route("/admin/call/callUser", methods=["POST"])
def expert_call_user_route():
    return CallService.expert_call_user()


@app.route("/admin/call/connect", methods=["POST"])
def connect_route():
    return CallService.connect()


# Below are the DataService routes, prefixed with /data
@app.route("/admin/data/errorlogs")
def get_error_logs_route():
    return DataService.get_error_logs()


@app.route("/admin/data/calls")
def get_calls_route():
    return DataService.get_all_calls()


@app.route("/admin/data/applications")
def get_applications_route():
    return DataService.get_applications()


@app.route("/admin/data/users")
def get_users_route():
    return DataService.get_users()


@app.route("/admin/data/experts")
def get_experts_route():
    return DataService.get_experts()


@app.route("/admin/data/categories")
def get_categories_route():
    return DataService.get_categories()


@app.route("/admin/data/schedules", methods=["POST", "GET"])
def schedules_route():
    return DataService.schedules()


# Below are the ExpertService routes, prefixed with /expert
@app.route("/admin/expert/experts/<string:id>", methods=["GET", "PUT", "DELETE"])
def handle_expert_route(id):
    return ExpertService.handle_expert(id)


@app.route("/admin/expert/popupData/<string:expertId>", methods=["GET"])
def get_popup_data_route(expertId):
    return ExpertService.get_popup_data(expertId)


# Below are the UserService routes, prefixed with /user
@app.route("/admin/user/leads", methods=["GET"])
def get_leads_route():
    return UserService.get_leads()


@app.route("/admin/user/users/<string:id>", methods=["GET", "PUT", "DELETE"])
def handle_user_route(id):
    return UserService.handle_user(id)


if __name__ == "__main__":
    app.run(port=8080)
