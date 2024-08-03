from typing import Literal
from flask import Blueprint
from flask.wrappers import Response
from Utils.Services.GameService import GameService

game_routes = Blueprint("games", __name__)
game_service = GameService()


@game_routes.route("/admin/games/addQuestion", methods=["POST"])
def add_question_route() -> tuple[Response, Literal[400]] | tuple[Response, Literal[200]]:
    return game_service.add_question()


@game_routes.route("/admin/games/quizQuestions", methods=["GET"])
def get_questions_route() -> tuple[Response, Literal[200]]:
    return game_service.get_questions()
