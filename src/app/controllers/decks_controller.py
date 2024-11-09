"""Module for handling decks-related endpoints."""

from flask import Blueprint, jsonify, request

from app.services.deck_service import DeckService


class DecksController:
    """class to control decks"""

    @staticmethod
    def create_deck():
        """create a new deck"""

        data = request.get_json()

        if "name" not in data:
            return jsonify({"error": "Missing required information"}), 400
        image = None

        result = DeckService.create_deck(data["name"], data["masterdeck_id"], image)
        return jsonify(result), 200

    @staticmethod
    def get_all_decks():
        """Get all decks"""

        result = DeckService.get_all_decks()
        return jsonify(result), 200

    @staticmethod
    def get_decks_by_masterdeck_id():
        """This method get decks by user_id"""

        masterdeck_id = request.args.get("masterdeck_id")
        user_id = request.args.get("user_id")

        if not masterdeck_id or not user_id:
            return jsonify({"error": "info is required"}), 400

        result = DeckService.get_decks_by_masterdeck_id(masterdeck_id, user_id)
        return jsonify(result), 200


decks_blueprint = Blueprint("decks_blueprint", __name__)

decks_blueprint.route("/create", methods=["POST"])(DecksController.create_deck)
decks_blueprint.route("/get", methods=["GET"])(DecksController.get_all_decks)
decks_blueprint.route("/get_by_masterdeck_id", methods=["GET"])(
    DecksController.get_decks_by_masterdeck_id
)
