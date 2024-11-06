from flask import Blueprint
from ..controllers.auth_controller import auth_blueprint
from ..controllers.masterdecks_controller import masterdeck_blueprint
from ..controllers.decks_controller import decks_blueprint
from ..controllers.card_controller import card_blueprint
from ..controllers.user_progress_controller import user_progress_blueprint


routes = Blueprint('main', __name__)


routes.register_blueprint(auth_blueprint, url_prefix='/auth')
routes.register_blueprint(masterdeck_blueprint, url_prefix='/masterdeck')
routes.register_blueprint(decks_blueprint, url_prefix='/deck')
routes.register_blueprint(card_blueprint, url_prefix='/card')
routes.register_blueprint(user_progress_blueprint, url_prefix='/progress')

