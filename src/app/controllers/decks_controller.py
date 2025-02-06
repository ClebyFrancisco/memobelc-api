"""Module for handling decks-related endpoints."""

from flask import Blueprint, jsonify, request

from src.app.services.deck_service import DeckService


class DecksController:
    """class to control decks"""

    @staticmethod
    def create_deck():
        """create a new deck"""

        data = request.get_json()

        if "name" or "collection_id" not in data:
            return jsonify({"error": "Missing required information"}), 400
        image = None

        result = DeckService.create_deck(data["name"], data["collection_id"], image)
        return jsonify(result), 200

    @staticmethod
    def get_all_decks():
        """Get all decks"""

        result = DeckService.get_all_decks()
        return jsonify(result), 200

    @staticmethod
    def get_decks_by_collection_id():
        """This method get decks by user_id"""

        collection_id = request.args.get("collection_id")
        user_id = request.args.get("user_id")

        if not collection_id or not user_id:
            return jsonify({"error": "info is required"}), 400

        result = DeckService.get_decks_by_collection_id(collection_id, user_id)
        return jsonify(result), 200


decks_blueprint = Blueprint("decks_blueprint", __name__)

decks_blueprint.route("/create", methods=["POST"])(DecksController.create_deck)
decks_blueprint.route("/get", methods=["GET"])(DecksController.get_all_decks)
decks_blueprint.route("/get_by_collection_id", methods=["GET"])(
    DecksController.get_decks_by_collection_id
)
