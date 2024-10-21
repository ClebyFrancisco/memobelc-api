from os import environ, path
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

class Config:
    MONGO_URI = environ.get('MONGO_URI') or "mongodb://localhost:27017/memobelc"
    SECRET_KEY = environ.get('SECRET_KEY')
    
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = 'memobelc@ybelc.com'
    
    FLASK_ENV = 'development'
    


    
    