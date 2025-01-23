from dotenv import load_dotenv
from os import path, environ

basedir = path.abspath(path.join(path.dirname(__file__), "../../"))
load_dotenv(path.join(basedir, ".env"))


class Config:
    PYTHONPATH = "src"
    MONGO_URI = environ["MONGO_URI"]
    SECRET_KEY = environ["SECRET_KEY"]

    MAIL_SERVER = environ["MAIL_SERVER"]
    
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = environ["MAIL_USERNAME"]
    MAIL_PASSWORD = environ["MAIL_PASSWORD"]
    MAIL_DEFAULT_SENDER = environ["MAIL_DEFAULT_SENDER"]

    FLASK_ENV = "development"
