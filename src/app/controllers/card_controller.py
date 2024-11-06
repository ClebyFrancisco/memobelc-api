from flask import Blueprint, jsonify, request
from ..services.card_service import CardService

class CardController:
    @staticmethod
    def create_card():
        data = request.get_json()
        if not data.get("front") or not data.get("back"):
            return jsonify({"error": "Campos 'front' e 'back' são obrigatórios"}), 400

        result = CardService.create_card(data)
        return jsonify(result), 201

    @staticmethod
    def get_card(card_id):
        result = CardService.get_card_by_id(card_id)
        if result:
            return jsonify(result), 200
        return jsonify({"error": "Card não encontrado"}), 404

    @staticmethod
    def get_all_cards():
        result = CardService.get_all_cards()
        return jsonify(result), 200

    @staticmethod
    def update_card(card_id):
        data = request.get_json()
        result = CardService.update_card(card_id, data)
        if result:
            return jsonify(result), 200
        return jsonify({"error": "Card não encontrado"}), 404

    @staticmethod
    def delete_card(card_id):
        if CardService.delete_card(card_id):
            return jsonify({"message": "Card excluído com sucesso"}), 200
        return jsonify({"error": "Card não encontrado"}), 404


# Blueprint para rotas de Card
card_blueprint = Blueprint("card_blueprint", __name__)

# Definindo as rotas
card_blueprint.route("/", methods=["POST"])(CardController.create_card)
card_blueprint.route("/", methods=["GET"])(CardController.get_all_cards)

card_blueprint.route("/<string:card_id>", methods=["GET"])(CardController.get_card)
card_blueprint.route("/<string:card_id>", methods=["PUT"])(CardController.update_card)
card_blueprint.route("/<string:card_id>", methods=["DELETE"])(CardController.delete_card)
