from flask import Blueprint
from ..controllers.auth_controller import auth_controller
from ..controllers.protected_controller import protected

routes = Blueprint('main', __name__)


routes.register_blueprint(auth_controller, url_prefix='/auth')

#@protected.route
routes.register_blueprint(protected)
