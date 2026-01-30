"""Module for handling userProgress-related endpoints."""

from flask import Blueprint, jsonify, request
from src.app.services.user_progress_service import UserProgressService


class UserProgressController:
    """Class to handle user progress operations"""

    @staticmethod
    def create_or_update_progress():
        """This method create or update a new progress or user"""

        data = request.get_json()
        user_id = data.get("user_id")
        deck_id = data.get("deck_id")
        card_id = data.get("card_id")

        if not all([user_id, deck_id, card_id]):
            return jsonify({"error": "Missing required information"}), 400

        UserProgressService.create_or_update_progress(user_id, deck_id, card_id)
        return jsonify({"message": "User progress updated successfully"}), 200

    @staticmethod
    def get_pending_cards():
        """This method retrieves all pending cards for a user"""

        user_id = request.args.get("user_id")
        deck_id = request.args.get("deck_id")

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        pending_cards = UserProgressService.get_pending_cards(user_id, deck_id)
        return jsonify({"pending_cards": pending_cards}), 200

    @staticmethod
    def update_card_status():
        """This method updates the status of multiple cards for a user"""
        
        data = request.get_json()
        user_id = data.get("user_id")
        cards = data.get("cards", [])

        if not user_id or not isinstance(cards, list) or not cards:
            return jsonify({"error": "Missing or invalid required information"}), 400

        updated_progress = []
        for card in cards:
            card_id = card.get("card_id")
            recall_level = card.get("recall_level")
            
            if card_id and recall_level is not None:
                progress = UserProgressService.update_card_status(
                    user_id, card_id, recall_level
                )
                if progress is not None:
                    updated_progress.append(progress)
        return jsonify({"updated_progress": updated_progress}), 200



# Blueprint para as rotas de progresso de usuário
user_progress_blueprint = Blueprint("user_progress_blueprint", __name__)

# Definindo as rotas
user_progress_blueprint.route("/", methods=["POST"])(
    UserProgressController.create_or_update_progress
)
user_progress_blueprint.route("/pending", methods=["GET"])(
    UserProgressController.get_pending_cards
)
user_progress_blueprint.route("/update_status", methods=["PUT"])(
    UserProgressController.update_card_status
)
