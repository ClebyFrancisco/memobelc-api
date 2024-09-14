# src/app/controllers/card_controller.py

from flask import Blueprint, request, jsonify
from ..middlewares.token_required import token_required
from ..services.card_service import CardService

class CardController:
    def __init__(self):
        self.card_bp = Blueprint('card', __name__)
        self.register_routes()

    def register_routes(self):
        @self.card_bp.route('/cards', methods=['POST'])
        @token_required
        def create_card(current_user):
            data = request.json
            front = data.get('front')
            back = data.get('back')
            card = self.card_service.create_card(front, back)
            return jsonify(card.to_dict()), 201

        @self.card_bp.route('/cards/<card_id>', methods=['GET'])
        @token_required
        def get_card(current_user, card_id):
            card = self.card_service.get_card_by_id(card_id)
            if card:
                return jsonify(card.to_dict())
            return jsonify({'error': 'Card not found'}), 404

        @self.card_bp.route('/cards/<card_id>', methods=['PUT'])
        @token_required
        def update_card(current_user, card_id):
            data = request.json
            front = data.get('front')
            back = data.get('back')
            card = self.card_service.update_card(card_id, front, back)
            if card:
                return jsonify(card.to_dict())
            return jsonify({'error': 'Card not found'}), 404

        @self.card_bp.route('/cards/<card_id>', methods=['DELETE'])
        @token_required
        def delete_card(current_user, card_id):
            self.card_service.delete_card(card_id)
            return jsonify({'message': 'Card deleted'}), 204

    @property
    def card_service(self):
        return CardService()

# Crie uma instância do controlador e adicione o Blueprint ao aplicativo
card_controller = CardController()
card_bp = card_controller.card_bp
