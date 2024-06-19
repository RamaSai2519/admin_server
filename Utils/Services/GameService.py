from Utils.Helpers.HelperFunctions import HelperFunctions as hf
from Utils.config import users_collection, experts_collection, players
from flask import request, jsonify, Response
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone
from bson import ObjectId
from pprint import pprint
import requests
import queue
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

    @staticmethod
    def room_stream():
        roomId = request.args.get("roomId")
        if not roomId:
            return jsonify({"message": "roomId query parameter is required"}), 400

        def event_stream():
            q = queue.Queue()
            if roomId not in players:
                players[roomId] = []
            players[roomId].append(q)
            try:
                while True:
                    try:
                        result = q.get()
                        yield f"data: {result}\n\n"
                    except queue.Empty:
                        yield "data: lalala \n\n"
            except GeneratorExit:
                if roomId in players and q in players[roomId]:
                    players[roomId].remove(q)
                raise
            except BrokenPipeError:
                if roomId in players and q in players[roomId]:
                    players[roomId].remove(q)
                raise

        return Response(event_stream(), content_type="text/event-stream")

    @staticmethod
    def watch_room_changes():
        with devdb["gameRooms"].watch([{'$match': {'operationType': 'update'}}]) as stream:
            for change in stream:
                pprint(change)
                print(change['documentKey'])
                doc_id = change["documentKey"]["_id"]
                doc = devdb["gameRooms"].find_one({"_id": doc_id})
                roomId = doc["roomId"]
                status = doc["status"]
                if status is True:
                    if roomId in players:
                        for player in players[roomId]:
                            player.put("Game Started")

    @staticmethod
    def close_room_connections():
        for roomId in list(players.keys()):
            for q in players[roomId]:
                q.put("Game Ended")
        players.pop(roomId)

    @staticmethod
    def room_status():
        data = request.json
        roomId = data["roomId"]
        userId = data["userId"]
        saarthiId = data["saarthiId"]
        role = data["role"]

        if role == "user":
            current_time = datetime.now(timezone.utc)
            result = devdb["gameRooms"].find_one_and_update(
                {"roomId": roomId},
                {"$setOnInsert": {
                    "roomId": roomId,
                    "user": userId,
                    "saarthi": saarthiId,
                    "status": False,
                    "createdTime": current_time
                }},
                upsert=True,
                return_document=True
            )

            if result and result.get("status") is False:
                return jsonify({"message": "Please wait..."}), 200
            elif result:
                return jsonify({"message": "Room already exists"}), 400
            else:
                print("Room created when user asked")
                return jsonify({"message": "Room created"}), 200

        elif role == "saarthi":
            room = devdb["gameRooms"].find_one({"roomId": roomId})
            if room:
                devdb["gameRooms"].update_one({"roomId": roomId}, {
                    "$set": {"status": True}
                })
                return jsonify({"message": "Room status updated"}), 200
            else:
                return jsonify({"message": "Room not found"}), 400
        else:
            return jsonify({"message": "Invalid role"}), 400
