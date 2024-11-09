import jwt
import datetime
from flask import current_app, jsonify
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from src.app import mail

from app.models.user_model import UserModel
from app.proto.pb.auth import LoginResponse


class AuthService:

    @staticmethod
    def create_user(name, email, password):
        if UserModel.find_by_email(email):
            return None
        hashed_password = generate_password_hash(password)

        UserModel(name=name, email=email, password=hashed_password).save_to_db()
        user = UserModel.find_by_email(email)

        if user:
            token = jwt.encode(
                {
                    "_id": user._id,
                    "email": user.email,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=72),
                },
                current_app.config["SECRET_KEY"],
                algorithm="HS256",
            )
            code = UserModel.generate_code(email)
            AuthService.send_confirm_email(email, code)
            return token
        return None

    @staticmethod
    def authenticate_user(email, password):
        user = UserModel.find_by_email(email)
        is_confirmed = UserModel.verify_is_confirmed(user.email)
        if user and check_password_hash(user.password, password):
            token = jwt.encode(
                {
                    "_id": user._id,
                    "email": user.email,
                    "exp": datetime.datetime.utcnow()
                    + datetime.timedelta(hours=72 if is_confirmed else 0.25),
                },
                current_app.config["SECRET_KEY"],
                algorithm="HS256",
            )

            if is_confirmed:
                if current_app.config["FLASK_ENV"] == "development":
                    return {"token": token, "name": user.name, "email": user.email}
                else:
                    return LoginResponse(token=token, name=user.name, email=user.email)
            else:
                code = UserModel.generate_code(email)
                AuthService.send_confirm_email(email, code)
                if current_app.config["FLASK_ENV"] == "development":
                    return {"pending": ["O Usuário não está confirmado!", token]}
                else:
                    return ErrorResponse(erro="O Usuário não está confirmado!")

        return None

    @staticmethod
    def verify_code(user, code):
        code = UserModel.verify_code(user.email, code)
        if code:
            UserModel.turn_confirmed(user.email)
            return True
        else:
            return False

    @staticmethod
    def refresh_token(token):
        data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        user = UserModel.find_by_email(data["email"])

        if user:
            token = jwt.encode(
                {
                    "_id": user._id,
                    "email": user.email,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=72),
                },
                current_app.config["SECRET_KEY"],
                algorithm="HS256",
            )

        if current_app.config["FLASK_ENV"] == "development":
            return {"token": token, "name": user.name, "email": user.email}
        else:
            return LoginResponse(token=token, name=user.name, email=user.email)

        return None

    @staticmethod
    def send_confirm_email(email, code):
        msg = Message("Assunto Teste", recipients=[email])
        msg.body = f"Aqui está seu codigo de validação: {code}"

        mail.send(msg)

        return "E-mail enviado!"

    @staticmethod
    def forgot_password(email):
        user = UserModel.find_by_email(email)

        if not user:
            return None

        code = UserModel.generate_code(email)
        AuthService.send_confirm_email(email, code)
        token_code = jwt.encode(
            {
                "email": user.email,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        return jsonify({"token": token_code}), 200
