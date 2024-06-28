from Utils.Services.ContentService import ContentService
from flask_jwt_extended import jwt_required
from flask import Blueprint

content_routes = Blueprint("content_routes", __name__)


@content_routes.route("/admin/content/shorts", methods=["GET"])
@jwt_required()
def get_contents_route():
    return ContentService.get_shorts()


@content_routes.route("/admin/content/videoUrl", methods=["GET"])
@jwt_required()
def get_video_url_route():
    return ContentService.get_video_url()


@content_routes.route("/admin/content/Video", methods=["POST"])
@jwt_required()
def approve_video_route():
    return ContentService.approve_video()
