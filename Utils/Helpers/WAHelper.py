from Utils.config import watemplates_collection, temp_collection
from bson.objectid import ObjectId
from datetime import datetime
import requests
import json


class WAHelper:
    def __init__(self):
        self.driver = None
        self.waUrl = "https://6x4j0qxbmk.execute-api.ap-south-1.amazonaws.com/main/actions/send_whatsapp"

    def format_input(self, inputs: dict) -> dict:
        output_dict = {}
        for key, value in inputs.items():
            new_key = key.replace('<', '').replace('>', '')
            output_dict[new_key] = value
        return output_dict

    def prepare_payload(self, user: dict, templateId: str, inputs: dict) -> dict:
        template = self.find_template(templateId)
        if template == "":
            return {}
        inputs = self.format_input(inputs)
        if "user_name" in inputs:
            inputs["user_name"] = user["name"] if "name" in user else "User"
        payload = {
            "phone_number": user["phoneNumber"],
            "template_name": template,
            "parameters": inputs
        }
        return payload

    def find_template(self, templateId: str) -> str:
        template = watemplates_collection.find_one(
            {"_id": ObjectId(templateId)})
        if not template:
            return ""
        template = template["name"]
        return template

    def send_whatsapp_message(self, payload: dict, messageId: str, phoneNumber: str) -> requests.Response:
        headers = {'Content-Type': 'application/json'}
        response = requests.request(
            "POST", self.waUrl, headers=headers, data=json.dumps(payload))
        temp_collection.insert_one({
                    "phoneNumber": phoneNumber,
                    "responseCode": response.status_code,
                    "responseText": response.text,
                    "messageId": messageId,
                    "datetime": datetime.now()
                })
        return response
