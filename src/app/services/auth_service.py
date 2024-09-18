import jwt
import datetime
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

from ..models.user_model import UserModel
from ..proto.pb.auth import LoginResponse

class AuthService:
    def __init__(self):
        pass 

    def create_user(self, name, email, password):
        if UserModel.find_by_email(email):
            return None
        hashed_password = generate_password_hash(password)
        return UserModel(name=name, email=email, password=hashed_password).save_to_db()

    def authenticate_user(self, email, password):
        user = UserModel.find_by_email(email)
        if user and check_password_hash(user.password, password):
            token = jwt.encode({
                '_id': user._id,
                'email': user.email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=72)
            }, current_app.config['SECRET_KEY'], algorithm="HS256")
            
            if current_app.config['FLASK_ENV'] == 'development':
                return token
            else:
                return LoginResponse(token=token)
        return None
