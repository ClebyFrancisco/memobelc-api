"""Module for handling authentication-related endpoints.

This module contains the AuthController class, which provides user registration,
login, token refresh, and code verification functionalities. Each method is set up
to handle both JSON and protobuf data formats, depending on the environment.
"""

from flask import Blueprint, jsonify, request, Response, current_app
from app.services.auth_service import AuthService
from app.middlewares.token_required import token_required
from app.proto.pb.auth import (
    LoginRequest,
    RefreshToken,
    RegisterRequest,
    RegisterResponse,
    ErrorResponse,
    CodeRequest,
)


class AuthController:
    """Class to handle user authentication operations,
    such as registering, logging in, and refreshing tokens."""

    @staticmethod
    def register():
        """Registers a new user.

        If in development environment, this method handles JSON data directly;
        otherwise, it parses the protobuf data for user registration.
        Returns a JSON response or protobuf response with user creation status.
        """
        if current_app.config["FLASK_ENV"] == "development":
            data = request.get_json()

            if (
                not data
                or "email" not in data
                or "password" not in data
                or "name" not in data
            ):
                return jsonify({"error": "Missing required information"}), 400

            user = AuthService.create_user(
                data["name"], data["email"], data["password"]
            )
            if user:
                return jsonify({"message": "User created successfully"}), 201

            return jsonify({"error": "User already exists"}), 400

        data = request.data
        register_request = RegisterRequest().parse(data)

        if (
            not register_request.email
            or not register_request.password
            or not register_request.name
        ):
            error_response = ErrorResponse(error="pending information")
            return Response(
                bytes(error_response), status=400, mimetype="application/x-protobuf"
            )

        user = AuthService.create_user(
            register_request.name, register_request.email, register_request.password
        )
        if user:
            serialized_response = bytes(RegisterResponse(message=user))
            return Response(
                serialized_response, mimetype="application/octet-stream", status=201
            )

        serialized_response = bytes(ErrorResponse(error="User already exists"))
        return Response(
            serialized_response, mimetype="application/octet-stream", status=400
        )

    @staticmethod
    def login():
        """Authenticates a user."""
        if current_app.config["FLASK_ENV"] == "development":
            data = request.get_json()

            if not data or "email" not in data or "password" not in data:
                return jsonify({"error": "Email and password are required"}), 400

            token = AuthService.authenticate_user(data["email"], data["password"])
            if token:
                return jsonify(token), 200

            return jsonify({"error": "Invalid credentials"}), 401

        data = request.data
        login_request = LoginRequest().parse(data)

        if not login_request.email or not login_request.password:
            error_response = ErrorResponse(error="Email and password are required")
            return Response(
                bytes(error_response), status=400, mimetype="application/x-protobuf"
            )

        token = AuthService.authenticate_user(
            login_request.email, login_request.password
        )
        if token:
            serialized_response = bytes(token)
            return Response(
                serialized_response, mimetype="application/octet-stream", status=200
            )

        return None  # Added return None to handle R1710 lint error

    @staticmethod
    def refresh_token():
        """Refreshes an authentication token."""
        if current_app.config["FLASK_ENV"] == "development":
            data = request.get_json()

            if not data or "token" not in data:
                return jsonify({"error": "token is required"}), 400

            token = AuthService.refresh_token(data["token"])
            if token:
                return jsonify(token), 200

            return jsonify({"error": "Invalid credentials"}), 401

        data = request.data
        refresh_request = RefreshToken().parse(data)

        if not refresh_request.token:
            error_response = ErrorResponse(error="token is missing")
            return Response(
                bytes(error_response), status=400, mimetype="application/x-protobuf"
            )

        token = AuthService.refresh_token(refresh_request.token)
        if token:
            serialized_response = bytes(token)
            return Response(
                serialized_response, mimetype="application/octet-stream", status=200
            )

        return None  # Added return None to handle R1710 lint error

    @staticmethod
    @token_required
    def verify_code(current_user, token):
        """Verifies a code for the current user."""
        if current_app.config["FLASK_ENV"] == "development":
            data = request.get_json()
            response = AuthService.verify_code(current_user, data["code"])

            if response:
                token = AuthService.refresh_token(token)
                return jsonify(token), 200

            return jsonify("Invalid code"), 401

        data = request.data
        code_request = CodeRequest().parse(data)

        if not code_request.code:
            error_response = ErrorResponse(error="code is missing")
            return Response(
                bytes(error_response), status=400, mimetype="application/x-protobuf"
            )

        response = AuthService.verify_code(current_user, code_request.code)
        if response:
            token = AuthService.refresh_token(token)
            if token:
                serialized_response = bytes(token)
                return Response(
                    serialized_response, mimetype="application/octet-stream", status=200
                )

            error_response = ErrorResponse(error="Invalid token")
            return Response(
                bytes(error_response), status=401, mimetype="application/x-protobuf"
            )

        error_response = ErrorResponse(error="Invalid code")
        return Response(
            bytes(error_response), status=401, mimetype="application/x-protobuf"
        )

    @staticmethod
    def forgot_password():
        """Handles forgotten password requests."""
        data = request.get_json()

        if "email" not in data:
            return jsonify({"error": "Email and password are required"}), 400

        return AuthService.forgot_password(data["email"])


# Blueprint for authentication routes
auth_blueprint = Blueprint("auth_blueprint", __name__)

# Defining routes
auth_blueprint.route("/register", methods=["POST"])(AuthController.register)
auth_blueprint.route("/login", methods=["POST"])(AuthController.login)
auth_blueprint.route("/refresh_token", methods=["POST"])(AuthController.refresh_token)
auth_blueprint.route("/verify_code", methods=["POST"])(AuthController.verify_code)
auth_blueprint.route("/forgot_password", methods=["POST"])(
    AuthController.forgot_password
)
