from dotenv import load_dotenv
from os import path, environ

basedir = path.abspath(path.join(path.dirname(__file__), "../../"))
load_dotenv(path.join(basedir, ".env"))


class Config:
    PYTHONPATH = "src"
    MONGO_URI = environ["MONGO_URI"]
    SECRET_KEY = environ["SECRET_KEY"]
    STRIPE_SECRET_KEY = environ["STRIPE_SECRET_KEY"]
    PRICE_ID = environ['PRICE_ID']
    STRIPE_WHSEC = environ["STRIPE_WHSEC"]
    GENAI_API_KEY = environ["GENAI_API_KEY"]

    MAIL_SERVER = environ["MAIL_SERVER"]
    MAIL_PORT = environ["MAIL_PORT"]
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = environ["MAIL_USERNAME"]
    MAIL_PASSWORD = environ["MAIL_PASSWORD"]
    MAIL_DEFAULT_SENDER = environ["MAIL_DEFAULT_SENDER"]
    
    FRONT_BASE_URL = environ["FRONT_BASE_URL"]

    FLASK_ENV = "development"
    PORT = int(environ["PORT"])



