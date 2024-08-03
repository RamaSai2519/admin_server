import threading
from flask import Flask
from flask_cors import CORS
from datetime import timedelta
from routes.wa_routes import wa_routes
from Utils.config import JWT_SECRET_KEY
from flask_jwt_extended import JWTManager
from routes.auth_routes import auth_routes
from routes.call_routes import call_routes
from routes.data_routes import data_routes
from routes.game_routes import game_routes
from routes.user_routes import user_routes
from routes.event_routes import event_routes
from routes.expert_routes import expert_routes
from routes.content_routes import content_routes
from routes.service_routes import service_routes
from routes.schedule_routes import schedule_routes
from Utils.Services.ExpertService import ExpertService

app = Flask(__name__)

JWTManager(app)
CORS(app, supports_credentials=True)

app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=1)

threading.Thread(target=ExpertService.watch_changes, daemon=True).start()
threading.Thread(
    target=ExpertService.periodic_reset_sse_connections, daemon=True).start()

app.register_blueprint(wa_routes)
app.register_blueprint(auth_routes)
app.register_blueprint(call_routes)
app.register_blueprint(data_routes)
app.register_blueprint(game_routes)
app.register_blueprint(user_routes)
app.register_blueprint(event_routes)
app.register_blueprint(expert_routes)
app.register_blueprint(content_routes)
app.register_blueprint(service_routes)
app.register_blueprint(schedule_routes)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080,
        debug=True,
    )
