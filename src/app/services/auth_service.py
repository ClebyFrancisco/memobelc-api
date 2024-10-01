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
            
            is_confirmed = UserModel.verify_is_confirmed(user.email)
            if is_confirmed:
                if current_app.config['FLASK_ENV'] == 'development':
                    return {'token': token, 'name':user.name, 'email':user.email}
                else:
                    return LoginResponse(token=token, name=user.name, email=user.email)
            else:
                if current_app.config['FLASK_ENV'] == 'development':
                    return {'pending': "O Usuário não está confirmado!" }
                else:
                    return ErrorResponse(erro="O Usuário não está confirmado!")
                
            

            
        return None
    def refresh_token(self, token):
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        user = UserModel.find_by_email(data['email'])
        
        if user:
            token = jwt.encode({
                '_id': user._id,
                'email': user.email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=72)
            }, current_app.config['SECRET_KEY'], algorithm="HS256")
            
            
        if current_app.config['FLASK_ENV'] == 'development':
            return {'token': token, 'name':user.name, 'email':user.email}
        else:
            return LoginResponse(token=token, name=user.name, email=user.email)
            
        return None
    
        def confirm_email(token):
            try:
                email = s.loads(token, salt='email-confirm', max_age=3600)  # O token expira em 1 hora
                user = db.users.find_one({'email': email})
                if user and not user['is_confirmed']:
                    db.users.update_one({'email': email}, {'$set': {'is_confirmed': True}})
                    return jsonify({"message": "Email confirmado com sucesso."}), 200
                else:
                    return jsonify({"message": "Email já confirmado ou inválido."}), 400
            except Exception as e:
                return jsonify({"message": "Token inválido ou expirado."}), 400
    
    def updated_password(self, _id, new_password):
        pass
