from flask import Blueprint, jsonify, request, Response, current_app
from ..services.deck_service import DeckService

class DecksController():
    @staticmethod
    def createDeck():
        data = request.get_json()

        # Verificação de campos obrigatórios
        if 'name' not in data:
            return jsonify({'error': 'Missing required information'}), 400

        result = DeckService.create_deck(data['name'])
        return jsonify(result), 200
    
    def get_all_decks():
        result = DeckService.get_all_decks()
        return jsonify(result), 200 


# Blueprint para as rotas de autenticação
decks_blueprint = Blueprint('decks_blueprint', __name__)

# Definindo as rotas
decks_blueprint.route('/create', methods=['POST'])(DecksController.createDeck)
decks_blueprint.route('/get', methods=['GET'])(DecksController.get_all_decks)