from flask import Blueprint
from Utils.Services.GameService import GameService

game_routes = Blueprint("games", __name__)


@game_routes.route("/admin/games/profiles", methods=["GET"])
def get_profiles_route():
    return GameService.get_profiles()


@game_routes.route("/admin/games/addQuestion", methods=["POST"])
def add_question_route():
    return GameService.add_question()


@game_routes.route("/admin/games/quizQuestions", methods=["GET"])
def get_questions_route():
    return GameService.get_questions()


@game_routes.route("/admin/games/roomStatus", methods=["GET", "POST"])
def room_status_route():
    return GameService.room_status()


@game_routes.route("/admin/games/gameStatus", methods=["GET", "POST"])
def game_status_route():
    return GameService.game_status()


@game_routes.route("/admin/games/roomStream")
def room_stream_route():
    return GameService.room_stream()


@game_routes.route("/admin/games/gameConfig", methods=["GET"])
def game_config_route():
    return GameService.game_config()


@game_routes.route("/admin/games/question", methods=["POST"])
def question_decider_route():
    return GameService.question_decider()

@game_routes.route("/admin/games/details", methods=["GET"])
def get_details_route():
    return GameService.game_details()
