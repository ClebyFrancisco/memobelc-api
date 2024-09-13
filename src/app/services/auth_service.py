import jwt
import datetime
from ..models.user_model import find_user_by_email, create_user_in_db
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

def create_user(name, email, password):
    if find_user_by_email(email):
        return None
    hashed_password = generate_password_hash(password)
    return create_user_in_db(name, email, hashed_password)

def authenticate_user(email, password):
    user = find_user_by_email(email)
    if user and check_password_hash(user['password'], password):
        token = jwt.encode({
            'name': user['name'],
            'email': user['email'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=72)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")
        return token
    return None
