from flask import Blueprint
from ..controllers.auth_controller import auth_blueprint
from ..controllers.protected_controller import protected_bp
from ..controllers.card_controller import card_bp

routes = Blueprint('main', __name__)


routes.register_blueprint(auth_blueprint, url_prefix='/auth')

#@protected.route
routes.register_blueprint(protected_bp)
routes.register_blueprint(card_bp)
