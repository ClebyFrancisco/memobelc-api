from flask import Blueprint
from src.app.controllers.auth_controller import auth_blueprint
from src.app.controllers.collections_controller import collection_blueprint
from src.app.controllers.decks_controller import decks_blueprint
from src.app.controllers.card_controller import card_blueprint
from src.app.controllers.user_progress_controller import user_progress_blueprint
from src.app.controllers.videos_controller import video_blueprint
from src.app.controllers.chat_controller import chat_blueprint


routes = Blueprint("main", __name__)


routes.register_blueprint(auth_blueprint, url_prefix="/auth")
routes.register_blueprint(collection_blueprint, url_prefix="/collections")
routes.register_blueprint(decks_blueprint, url_prefix="/deck")
routes.register_blueprint(card_blueprint, url_prefix="/card")
routes.register_blueprint(video_blueprint, url_prefix="/video")
routes.register_blueprint(user_progress_blueprint, url_prefix="/progress")
routes.register_blueprint(chat_blueprint, url_prefix="/chat")
