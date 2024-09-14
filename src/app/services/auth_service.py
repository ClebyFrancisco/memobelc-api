import jwt
import datetime
from ..models.user_model import UserModel
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

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
                'id': user.id,
                'email': user.email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=72)
            }, current_app.config['SECRET_KEY'], algorithm="HS256")
            return token
        return None
