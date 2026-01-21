"""Module for handling user streak-related endpoints."""

from flask import Blueprint, jsonify
from src.app.middlewares.token_required import token_required
from src.app.services.user_streak_service import UserStreakService


class UserStreakController:
    """Class to handle user streak operations"""

    @staticmethod
    @token_required
    def get_streak(current_user, token):
        """Retorna informações sobre o streak atual do usuário."""
        result = UserStreakService.get_streak(str(current_user._id))
        return jsonify(result), 200


# Blueprint para as rotas
user_streak_blueprint = Blueprint("user_streak_blueprint", __name__)

# Definindo as rotas
user_streak_blueprint.route("/get", methods=["GET"])(
    UserStreakController.get_streak
)

