from flask import Blueprint
from ..controllers.auth_controller import auth_blueprint
from ..controllers.masterdecks_controller import masterdeck_blueprint
from ..controllers.decks_controller import decks_blueprint
from ..controllers.protected_controller import protected_bp
from ..controllers.card_controller import card_bp

routes = Blueprint('main', __name__)


routes.register_blueprint(auth_blueprint, url_prefix='/auth')
routes.register_blueprint(masterdeck_blueprint, url_prefix='/masterdeck')
routes.register_blueprint(decks_blueprint, url_prefix='/deck')

#@protected.route
routes.register_blueprint(protected_bp)
routes.register_blueprint(card_bp)
