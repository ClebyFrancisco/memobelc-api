import jwt
from datetime import datetime, timedelta, timezone
from flask import current_app
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from src.app import mail
from src.app.models.user_model import UserModel


class AuthService:
    """Handles user authentication, including registration, login, and token management."""

    @staticmethod
    def create_user(name, email, password):
        """Creates a new user and returns an authentication token."""
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
                    "exp": datetime.now(timezone.utc) + timedelta(hours=72),
                },
                current_app.config["SECRET_KEY"],
                algorithm="HS256",
            )
            AuthService.send_confirm_email(email, UserModel.generate_code(email))
            return token

        return None

    @staticmethod
    def authenticate_user(email, password):
        """Authenticates a user and returns an access token."""
        user = UserModel.find_by_email(email)
        if user and check_password_hash(user.password, password):
            is_confirmed = UserModel.verify_is_confirmed(user.email)
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

            return {"token": token, "name": user.name, "email": user.email, "user_id": user._id} if is_confirmed else {"pending": "User not confirmed!"}

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
                return {"token": token, "name": user.name, "email": user.email, "user_id": user._id}

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
        """Handles password recovery by sending a verification code."""
        user = UserModel.find_by_email(email)
        if not user:
            return None

        code = UserModel.generate_code(email)
        AuthService.send_confirm_email(email, code)
        token_code = jwt.encode(
            {
                "email": user.email,
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        return {"token": token_code}
