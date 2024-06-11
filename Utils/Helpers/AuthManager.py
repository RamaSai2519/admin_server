from flask_jwt_extended import get_jwt_identity
from datetime import datetime, timedelta
import jwt


class AuthManager:
    @staticmethod
    def generate_token(name, user_id, phone_number):
        payload = {
            "name": name,
            "userId": user_id,
            "phoneNumber": phone_number,
            "exp": datetime.now() + timedelta(seconds=24 * 60 * 60),
        }
        secret_key = "saltDemaze"
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return token

    @staticmethod
    def get_identity():
        identity = get_jwt_identity()
        return identity