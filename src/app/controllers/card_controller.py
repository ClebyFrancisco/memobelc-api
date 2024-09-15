from flask import Blueprint, jsonify, request
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
            """Cria um novo card"""
            data = request.get_json()
            front = data.get('front')
            back = data.get('back')

            if not front or not back:
                return jsonify({'error': 'Both front and back are required'}), 400

            card = CardService.create_card(front=front, back=back)
            return jsonify(card.to_dict()), 201

        @self.card_bp.route('/cards/<card_id>', methods=['GET'])
        @token_required
        def get_card(current_user, card_id):
            """Busca um card pelo ID"""
            card = CardService.get_card_by_id(card_id)
            if card:
                return jsonify(card.to_dict())
            return jsonify({'error': 'Card not found'}), 404

        @self.card_bp.route('/cards/<card_id>/performance', methods=['PUT'])
        @token_required
        def update_card_performance(current_user, card_id):
            """Atualiza o desempenho de um card"""
            data = request.get_json()
            success = data.get('success', False)

            card = CardService.update_card_performance(card_id, success)
            if card:
                return jsonify(card.to_dict())
            return jsonify({'error': 'Card not found'}), 404

        @self.card_bp.route('/cards/<card_id>', methods=['DELETE'])
        @token_required
        def delete_card(current_user, card_id):
            """Deleta um card"""
            deleted = CardService.delete_card(card_id)
            if deleted:
                return jsonify({'message': 'Card deleted successfully'})
            return jsonify({'error': 'Card not found'}), 404

# Crie uma instância do controlador e adicione o Blueprint ao aplicativo
card_controller = CardController()
card_bp = card_controller.card_bp
