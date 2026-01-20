from flask import Blueprint, jsonify, request, Response, current_app, abort
from werkzeug.exceptions import BadRequest, Unauthorized
from src.app.services.auth_service import AuthService
from src.app.middlewares.token_required import token_required


class AuthController:
    """Handles user authentication operations, including registration, login, token refresh, and code verification."""

    @staticmethod
    def register():
        """Registers a new user and returns a token upon success."""
        data = request.get_json()
        if not data or not all(k in data for k in ["email", "password", "name"]):
            return jsonify({"error": "Missing required information"}), 400

        token = AuthService.create_user(data["name"], data["email"].lower(), data["password"])
        return token

    @staticmethod
    def login():
        """Authenticates a user and returns an access token."""
        data = request.get_json()
        if not data or "email" not in data or "password" not in data:
            raise BadRequest(description="Email and password are required")

        token = AuthService.authenticate_user(data["email"].lower(), data["password"])
        if token:
            return jsonify(token), 200

        raise Unauthorized(description="Invalid credentials")

    @staticmethod
    def refresh_token():
        """Refreshes the authentication token."""
        data = request.get_json()
        if not data or "token" not in data:
            return jsonify({"error": "Token is required"}), 400

        token = AuthService.refresh_token(data["token"])
        if token:
            return jsonify(token), 200

        return jsonify({"error": "Invalid credentials"}), 401
                                                                                                                                                                                                                                                                                                                                                                
    @staticmethod
    @token_required
    def verify_code(current_user, token):
        """Verifies the user's validation code and refreshes the token if valid."""
        data = request.get_json()
        if not data or "code" not in data:
            return jsonify({"error": "Code is required"}), 400

        if AuthService.verify_code(current_user, data["code"]):
            token = AuthService.refresh_token(token)
            return jsonify(token), 200

        return jsonify({"error": "Invalid code"}), 401

    @staticmethod
    def forgot_password():
        """Handles password recovery requests."""
        data = request.get_json()
        if "email" not in data:
            return jsonify({"error": "Email is required"}), 400

        response = AuthService.forgot_password(data["email"])
        if response:
            
            return jsonify(response), 200
        return jsonify(), 400
    
    @staticmethod
    def reset_password():
        data = request.get_json()
        
        if not data or "password" not in data or 'token' not in data:
            raise BadRequest(description="Email and password are required")
        
        response = AuthService.reset_password(data['token'], data['password'])
        
        return response
    
    
    @staticmethod
    def save_user_access_log():
        data = request.get_json()
        
        if not data:
            return
        
        response = AuthService.save_user_access_log(data)
    @staticmethod
    def mail_list():
            
        data = request.get_json()
        if not data or not all(k in data for k in ["email"]):
            return jsonify({"error": "Missing required information"}), 400
        
        if "name" in data:
            name = data["name"]
        else:
            name = ''

        response = AuthService.mail_list(name, data["email"].lower())
        return response

    @staticmethod
    @token_required
    def logout(current_user, token):
        """Logout lógico da API: remove tokens de push do usuário para não receber notificações."""
        AuthService.logout_user(str(current_user._id))
        return jsonify({"message": "Logged out successfully"}), 200
        


auth_blueprint = Blueprint("auth_blueprint", __name__)

auth_blueprint.route("/register", methods=["POST"])(AuthController.register)
auth_blueprint.route("/login", methods=["POST"])(AuthController.login)
auth_blueprint.route("/refresh_token", methods=["POST"])(AuthController.refresh_token)
auth_blueprint.route("/verify_code", methods=["POST"])(AuthController.verify_code)
auth_blueprint.route("/forgot_password", methods=["POST"])(AuthController.forgot_password)
auth_blueprint.route("/reset_password", methods=["PUT"])(AuthController.reset_password)
auth_blueprint.route("/access_log", methods=['POST'])(AuthController.save_user_access_log)
auth_blueprint.route("/mail_list", methods=["POST"])(AuthController.mail_list)
auth_blueprint.route("/logout", methods=["POST"])(AuthController.logout)
