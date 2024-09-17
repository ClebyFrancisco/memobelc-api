from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
import os
from dotenv import load_dotenv
from .database.mongo import mongo
from .routes.routes import routes


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config['MONGO_URI'] = os.getenv('MONGO_URI')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    
    mongo.init_app(app)

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