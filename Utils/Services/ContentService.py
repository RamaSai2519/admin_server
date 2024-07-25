from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from Utils.Helpers.AuthManager import AuthManager as am
from Utils.config import shorts_collection, s3_client
from flask import jsonify, request
from bson import ObjectId
from pprint import pprint


class ContentService:
    @staticmethod
    def get_shorts():
        shorts = list(shorts_collection.find(
            {}, {"_id": 0, "categoryId": 0, "thumbnails": 0, "description": 0, "lastModifiedBy": 0}))
        pprint(shorts)
        return jsonify(shorts)

    @staticmethod
    def generate_presigned_url(bucket_name, object_key, expiration=3600):
        try:
            response = s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': bucket_name,
                                                                'Key': object_key,
                                                                'ResponseContentDisposition': 'inline'
                                                                },
                                                        ExpiresIn=expiration)
        except (NoCredentialsError, PartialCredentialsError) as e:
            print("Credentials not available:", e)
            return None
        return response

    @staticmethod
    def get_video_url():
        object_key = request.args.get('s3Key')
        bucket_name = 'sukoon-videos'
        url = ContentService.generate_presigned_url(bucket_name, object_key)

        if url:
            return jsonify({'url': url})
        else:
            return jsonify({'error': 'Failed to generate URL'}), 500

    @staticmethod
    def approve_video():
        video_id = request.args.get('videoId')
        status = request.args.get('status')
        if not video_id or not status:
            return jsonify({'msg': 'Missing videoId or status'}), 400

        shorts_collection.update_one({'videoId': video_id},
                                     {'$set': {'approved': True if status == 'true' else False, "lastModifiedBy": ObjectId(am.get_identity())}})
        return jsonify({'msg': 'Video status updated'})
