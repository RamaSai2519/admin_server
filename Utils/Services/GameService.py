from flask import request, jsonify
from flask.wrappers import Response
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import Literal
import requests
import json
import os

load_dotenv()

devclient = MongoClient(os.getenv("DEV_DB_URL"))
devdb = devclient["test"]
devgamesdb = devclient["games"]


class GameService:
    def __init__(self) -> None:
        self.questions_collection = devdb["quizquestions"]

    def add_question(self) -> tuple[Response, Literal[400]] | tuple[Response, Literal[200]]:
        data = request.json
        if not data:
            return jsonify({"message": "Missing data"}), 400
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
        headers = {'Content-Type': 'application/json'}

        response = requests.request(
            "POST", url, headers=headers, data=payload)

        if response.status_code != 200:
            return jsonify(response.json()), 400

        return jsonify({"message": "Question added successfully"}), 200

    def get_questions(self) -> tuple[Response, Literal[200]]:
        questions = list(self.questions_collection.find(
            {}, {"_id": 0, "options._id": 0}))

        return jsonify(questions), 200
