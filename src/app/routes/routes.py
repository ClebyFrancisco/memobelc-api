from flask import Blueprint
from ..controllers.auth_controller import auth_controller

routes = Blueprint('main', __name__)


routes.register_blueprint(auth_controller, url_prefix='/auth')
