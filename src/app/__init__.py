from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
from .database.mongo import mongo
from .provider.mail import mail
from .routes.routes import routes
from .config import Config
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    mongo.init_app(app)
    mail.init_app(app)

    SWAGGER_URL = "/doc"
    API_URL = "/static/swagger.json"
    SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
        SWAGGER_URL, API_URL, config={"app_name": "API Game Checkers"}
    )

    app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
    app.register_blueprint(routes)

    return app
