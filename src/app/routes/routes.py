from flask import Blueprint
from src.app.controllers.auth_controller import auth_blueprint
from src.app.controllers.collections_controller import collection_blueprint
from src.app.controllers.decks_controller import decks_blueprint
from src.app.controllers.card_controller import card_blueprint
from src.app.controllers.user_progress_controller import user_progress_blueprint
from src.app.controllers.videos_controller import video_blueprint
from src.app.controllers.chat_controller import chat_blueprint
from src.app.controllers.payment_controller import payment_blueprint
from src.app.controllers.classroom_controller import classroom_blueprint
from src.app.controllers.notification_controller import notification_blueprint
from src.app.controllers.user_streak_controller import user_streak_blueprint
from src.app.controllers.books_controller import books_blueprint
from src.app.controllers.invite_controller import invite_blueprint


routes = Blueprint("main", __name__)


routes.register_blueprint(auth_blueprint, url_prefix="/auth")
routes.register_blueprint(collection_blueprint, url_prefix="/collections")
routes.register_blueprint(decks_blueprint, url_prefix="/deck")
routes.register_blueprint(card_blueprint, url_prefix="/card")
routes.register_blueprint(video_blueprint, url_prefix="/video")
routes.register_blueprint(user_progress_blueprint, url_prefix="/progress")
routes.register_blueprint(chat_blueprint, url_prefix="/chat")
routes.register_blueprint(payment_blueprint, url_prefix="/payment")
routes.register_blueprint(classroom_blueprint, url_prefix="/classroom")
routes.register_blueprint(notification_blueprint, url_prefix="/notifications")
routes.register_blueprint(user_streak_blueprint, url_prefix="/streak")
routes.register_blueprint(books_blueprint, url_prefix="/books")
routes.register_blueprint(invite_blueprint, url_prefix="/invite")
