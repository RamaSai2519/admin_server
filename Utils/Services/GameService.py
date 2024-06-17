from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.config import users_collection, experts_collection
from flask import request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from bson import ObjectId
from pprint import pprint
import requests
import json
import os

load_dotenv()

devclient = MongoClient(os.getenv("DEV_DB_URL"))
devdb = devclient["test"]


class GameService:
    @staticmethod
    def get_profiles():
        userId = request.args.get("userId")
        expertId = request.args.get("expertId")

        user = users_collection.find_one({"_id": ObjectId(userId)})
        userName = hf.get_user_name(ObjectId(userId))

        expert = experts_collection.find_one({"_id": ObjectId(expertId)})
        expertName = hf.get_expert_name(ObjectId(expertId))

        if not user or not expert:
            return jsonify({"message": "Invalid user or expert"}), 400

        response = {
            "userName": userName,
            "expertName": expertName,
            "expertImage": expert["profile"]
        }

        return jsonify(response)

    @staticmethod
    def add_question():
        data = request.json
        payload = json.dumps({
            "question": data["question"],
            "options": [
                {"key": "1", "value": data["option1"],
                    "isCorrect": data["correctAnswer"] == data["option1"]},
                {"key": "2", "value": data["option2"],
                    "isCorrect": data["correctAnswer"] == data["option2"]},
                {"key": "3", "value": data["option3"],
                    "isCorrect": data["correctAnswer"] == data["option3"]},
                {"key": "4", "value": data["option4"],
                 "isCorrect": data["correctAnswer"] == data["option4"]}
            ],
            "level": int(data["level"]),
            "imageUrl": data["imageUrl"]
        })

        url = "https://4vd7p5pnjccfd35rcdr4zhrmq40rnryp.lambda-url.ap-south-1.on.aws/v1/quiz"

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request(
            "POST", url, headers=headers, data=payload)

        if response.status_code != 200:
            return jsonify(response.json()), 400

        return jsonify({"message": "Question added successfully"}), 200

    @staticmethod
    def get_questions():
        questions_collection = devdb["quizquestions"]

        questions = list(questions_collection.find(
            {}, {"_id": 0, "options._id": 0}))

        return jsonify(questions), 200
