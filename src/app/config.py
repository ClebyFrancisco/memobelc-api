from os import environ, path
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

class Config:
    MONGO_URI = environ.get('MONGO_URI') or "mongodb://localhost:27017/memobelc"
    SECRET_KEY = environ.get('SECRET_KEY')
    FLASK_ENV = environ.get('FLASK_ENV')