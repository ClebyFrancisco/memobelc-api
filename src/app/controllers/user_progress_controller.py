from flask import Blueprint, jsonify, request
from ..services.user_progress_service import UserProgressService

class UserProgressController:

    @staticmethod
    def create_or_update_progress():
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
        user_id = request.args.get("user_id")
        deck_id = request.args.get("deck_id")


        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        pending_cards = UserProgressService.get_pending_cards(user_id, deck_id)
        return jsonify({"pending_cards": pending_cards}), 200

    @staticmethod
    def update_card_status():
        data = request.get_json()
        user_id = data.get("user_id")
        deck_id = data.get("deck_id")
        card_id = data.get("card_id")

        if not all([user_id, deck_id, card_id]):
            return jsonify({"error": "Missing required information"}), 400

        updated_progress = UserProgressService.update_card_status(user_id, deck_id, card_id)
        return jsonify({"updated_progress": updated_progress}), 200

# Blueprint para as rotas de progresso de usuário
user_progress_blueprint = Blueprint("user_progress_blueprint", __name__)

# Definindo as rotas
user_progress_blueprint.route("/", methods=["POST"])(UserProgressController.create_or_update_progress)
user_progress_blueprint.route("/pending", methods=["GET"])(UserProgressController.get_pending_cards)
user_progress_blueprint.route("/update_status", methods=["PUT"])(UserProgressController.update_card_status)
