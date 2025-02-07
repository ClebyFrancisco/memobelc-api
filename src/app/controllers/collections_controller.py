"""Module for handling collections-related endpoints."""

from flask import Blueprint, jsonify, request, Response, current_app
from src.app.services.collections_service import CollectionService
from src.app.middlewares.token_required import token_required


class CollectionsController:
    """Class to handle collections operations"""

    @staticmethod
    def createCollection():
        """This method create a new collection"""

        data = request.get_json()

        if "name" not in data:
            return jsonify({"error": "Missing required information"}), 400

        if "user_id" in data:
            user = data["user_id"]
        else:
            user = None

        if "image" in data:
            image = data["image"]
        else:
            image = None

        result = CollectionService.create_collection(data["name"], image, user)
        return jsonify(result), 200

    @staticmethod
    def get_by_id(deck_id):
        """This method get a collection by id"""

        result = CollectionService.get_by_id(deck_id)
        return jsonify(result), 200

    @staticmethod
    @token_required
    def get_collections_by_user(current_user, token):
        """This method get collections by user_id"""

        result = CollectionService.get_collections_by_user(current_user._id)
        return jsonify(result), 200

    @staticmethod
    def get_all_collections():
        """This Method get all collections"""

        result = CollectionService.get_all_collections()
        return jsonify(result), 200

    @staticmethod
    def add_decks_to_collection(collection_id):
        """This method add a list of decks to collection"""

        data = request.get_json()

        if "deck_ids" not in data:
            return jsonify({"error": "Missing 'deck_ids' list"}), 400

        deck_ids = data["deck_ids"]

        success = CollectionService.add_decks_to_collection(collection_id, deck_ids)

        if success:
            return jsonify({"message": "Decks added successfully"}), 200
        else:
            return jsonify({"error": "Collection not found or no changes made"}), 404


# Blueprint para as rotas
collection_blueprint = Blueprint("collections_blueprint", __name__)

# Definindo as rotas
collection_blueprint.route("/create", methods=["POST"])(
    CollectionsController.createCollection
)
collection_blueprint.route("/get", methods=["GET"])(
    CollectionsController.get_all_collections
)
collection_blueprint.route("/get_by_user", methods=["GET"])(
    CollectionsController.get_collections_by_user
)
collection_blueprint.route("/get/<string:deck_id>", methods=["GET"])(
    CollectionsController.get_by_id
)
collection_blueprint.route("/add_decks/<string:collection_id>", methods=["PATCH"])(
    CollectionsController.add_decks_to_collection
)
