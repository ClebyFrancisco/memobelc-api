import jwt
from datetime import datetime, timedelta, timezone
from flask import current_app, jsonify
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from base64 import urlsafe_b64encode, urlsafe_b64decode
from werkzeug.exceptions import BadRequest, Unauthorized
from src.app import mail
from src.app.models.user_model import UserModel
from src.app.config import Config


class AuthService:
    """Handles user authentication, including registration, login, and token management."""

    @staticmethod
    def create_user(name, email, password):
        """Creates a new user and returns an authentication token."""
        if UserModel.find_by_email(email):
            return jsonify({"message": "User already exists!"}), 409

        hashed_password = generate_password_hash(password)
        UserModel(name=name, email=email, password=hashed_password).save_to_db()

        user = UserModel.find_by_email(email)
        if user:
            token = jwt.encode(
                {
                    "_id": user._id,
                    "email": user.email,
                    "exp": datetime.now(timezone.utc) + timedelta(hours=72),
                },
                current_app.config["SECRET_KEY"],
                algorithm="HS256",
            )
            AuthService.send_confirm_email(email, UserModel.generate_code(email))
            return jsonify({"message": "User created successfully", "token": token}), 201

        return BadRequest(description="An error has occurred!")

    @staticmethod
    def authenticate_user(email, password):
        """Authenticates a user and returns an access token."""
        user = UserModel.find_by_email(email)
        if user and check_password_hash(user.password, password):
            is_confirmed = UserModel.verify_is_confirmed(user.email)
            
            if not is_confirmed:
                AuthService.send_confirm_email(email, UserModel.generate_code(email))
            expiration = timedelta(hours=72 if is_confirmed else 0.25)

            token = jwt.encode(
                {
                    "_id": user._id,
                    "email": user.email,
                    "exp": datetime.now(timezone.utc) + expiration,
                },
                current_app.config["SECRET_KEY"],
                algorithm="HS256",
            )

            return {"token": token, "name": user.name, "email": user.email, "user_id": user._id, "role":user.role} if is_confirmed else {"pending": ["User not confirmed!", token]}

        return None

    @staticmethod
    def verify_code(user, code):
        """Verifies a user's validation code and confirms their account."""
        if UserModel.verify_code(user.email, code):
            UserModel.turn_confirmed(user.email)
            return True
        return False

    @staticmethod
    def refresh_token(token):
        """Refreshes the authentication token."""
        try:
            data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            user = UserModel.find_by_email(data["email"])

            if user:
                token = jwt.encode(
                    {
                        "_id": user._id,
                        "email": user.email,
                        "exp": datetime.now(timezone.utc) + timedelta(hours=72),
                    },
                    current_app.config["SECRET_KEY"],
                    algorithm="HS256",
                )
                return {"token": token, "name": user.name, "email": user.email, "user_id": user._id, "role":user.role}

        except jwt.ExpiredSignatureError:
            return None

        return None

    @staticmethod
    def send_confirm_email(email, code):
        """Sends a confirmation email with a verification code."""
        msg = Message("Account Verification", recipients=[email])
        msg.body = f"Your verification code is: {code}"
        mail.send(msg)
        return "Email sent!"

    @staticmethod
    def forgot_password(email):
        """Handles password recovery by sending a secure password reset link."""
        user = UserModel.find_by_email(email)
        if not user:
            return None

        
        encoded_id = urlsafe_b64encode(str(user._id).encode()).decode()

        
        reset_token = jwt.encode(
            {
                "reset_password": True,
                "user_id": encoded_id,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        
        base_frontend_url = Config.FRONT_BASE_URL
        reset_link = f"{base_frontend_url}/reset_password?token={reset_token}"

        msg = Message("Recuperação de senha", recipients=[email])
        msg.body = f"Olá!\n\nClique no link abaixo para redefinir sua senha. Esse link é válido por 15 minutos:\n\n{reset_link}\n\nSe você não solicitou isso, ignore este e-mail."
        mail.send(msg)
        

        return {"message": "E-mail de recuperação enviado com sucesso."}

    @staticmethod
    def reset_password(token, new_password):
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])

        if not payload.get("reset_password"):
            return {"error": "Token inválido para redefinição de senha."}, 400

           
        if datetime.fromtimestamp(payload["exp"], timezone.utc) < datetime.now(timezone.utc):
            return jsonify({"error": "Token expirado."}), 400
        
        decoded_id = urlsafe_b64decode(payload["user_id"].encode()).decode()
        hashed_password = generate_password_hash(new_password)
        
        
        response = UserModel.update_password(decoded_id, hashed_password)
        
        if response:
            return jsonify("Password updated successfully!"), 200