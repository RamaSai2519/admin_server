from Utils.Services.EngagementService import EngagementService
from Utils.Services.UserService import UserService
from flask_jwt_extended import jwt_required
from flask import Blueprint

user_routes = Blueprint("user_routes", __name__)
engagement_service = EngagementService()
user_service = UserService()


@user_routes.route("/admin/user/leads", methods=["GET", "POST"])
@jwt_required()
def get_leads_route():
    return user_service.get_leads()


@user_routes.route("/admin/user/leadRemarks", methods=["POST"])
@jwt_required()
def add_lead_remarks_route():
    return user_service.add_lead_remarks()


@user_routes.route("/admin/user/users/<string:id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_user_route(id):
    return user_service.handle_user(id)


@user_routes.route("/admin/user/engagementData", methods=["GET", "POST", "DELETE"])
@jwt_required()
def get_engagement_data_route():
    return engagement_service.get_engagement_data()
