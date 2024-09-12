from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
from src.app.routes.routes import routes


def create_app():
    app = Flask(__name__)
    
    SWAGGER_URL = '/doc'
    API_URL = '/static/swagger.json'
    SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "API Game Chechers"
        })
    
    
    app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
    app.register_blueprint(routes)

    return app