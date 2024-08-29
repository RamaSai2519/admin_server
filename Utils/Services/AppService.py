from Utils.config import (
    fcm_tokens_collection,
    ALLOWED_MIME_TYPES,
    s3_client
)
from Utils.Helpers.InsightsManager import InsightsManager as im
from Utils.Helpers.AuthManager import AuthManager as am
from werkzeug.utils import secure_filename
from flask import request, jsonify
from bson import ObjectId
import uuid
import os


class AppService:
    @staticmethod
    def get_insights():
        callInsights = im.create_insights_structures()
        return jsonify(callInsights)

    @staticmethod
    def save_fcm_token():
        data = request.json
        if not data:
            return jsonify({"error": "FCM token missing"}), 400
        token = data["token"]
        tokens = list(fcm_tokens_collection.find())
        if token in [t["token"] for t in tokens]:
            fcm_tokens_collection.update_one(
                {"token": token}, {
                    "$set": {"lastModifiedBy": ObjectId(am.get_identity())}}
            )
            return jsonify({"message": "FCM token already saved"}), 200
        elif token:
            fcm_tokens_collection.insert_one(
                {"token": token, "lastModifiedBy": ObjectId(am.get_identity())})
            return jsonify({"message": "FCM token saved successfully"}), 200
        else:
            return jsonify({"error": "FCM token missing"}), 400

    @staticmethod
    def file_filter(mimetype):
        return mimetype in ALLOWED_MIME_TYPES

    @staticmethod
    def upload():
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if not AppService.file_filter(file.mimetype):
            return jsonify({"error": "Invalid file type"}), 400

        try:
            story_id = str(uuid.uuid4())
            filename = secure_filename(file.filename).replace(   # type: ignore
                " ", "+")
            unique_filename = f"{int(os.times()[-1])}_{story_id}_{filename}"

            metadata = {
                "fieldName": file.name.lower().replace(" ", "+")  # type: ignore
            }

            s3_client.upload_fileobj(
                file,
                "sukoon-media",
                unique_filename,
                ExtraArgs={
                    "ACL": "public-read",
                    "Metadata": metadata,
                    "ContentType": file.mimetype
                }
            )

            file_url = s3_client.meta.endpoint_url + "/sukoon-media/" + unique_filename

            return jsonify({"message": "File uploaded successfully", "file_url": file_url})

        except Exception as e:
            return jsonify({"error": str(e)}), 500
