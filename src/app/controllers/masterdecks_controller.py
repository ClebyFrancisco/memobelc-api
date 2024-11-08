from flask import Blueprint, jsonify, request, Response, current_app
from ..services.masterdeck_service import MasterDeckService

class MasterDecksController():
    @staticmethod
    def createMasterDeck():
        data = request.get_json()

        # Verificação de campos obrigatórios
        if 'name' not in data:
            return jsonify({'error': 'Missing required information'}), 400
        

        
        if 'user_id' in data:
            user = data['user_id']
        else:
            user = None


        if 'image' in data:
            image = data['image']
        else:
            image = None

        result = MasterDeckService.create_masterdeck(data['name'], image, user)
        return jsonify(result), 200
    
    @staticmethod
    def get_by_id(deck_id):
        result = MasterDeckService.get_by_id(deck_id)
        return jsonify(result), 200 
    
    @staticmethod
    def get_masterdecks_by_user():
        user_id = request.args.get("user_id")

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        
        result = MasterDeckService.get_masterdecks_by_user(user_id)
        return jsonify(result), 200

    @staticmethod
    def get_all_masterdecks():
        result = MasterDeckService.get_all_masterdecks()
        return jsonify(result), 200
    
    @staticmethod
    def add_decks_to_masterdeck(masterdeck_id):
        """Adiciona uma lista de decks ao MasterDeck"""
        data = request.get_json()
        
        # Verifique se 'deck_ids' está presente nos dados
        if 'deck_ids' not in data:
            return jsonify({"error": "Missing 'deck_ids' list"}), 400
        
        deck_ids = data['deck_ids']
        
        # Atualize o MasterDeck com os IDs dos decks
        success = MasterDeckService.add_decks_to_masterdeck(masterdeck_id, deck_ids)
        
        if success:
            return jsonify({"message": "Decks added successfully"}), 200
        else:
            return jsonify({"error": "MasterDeck not found or no changes made"}), 404


# Blueprint para as rotas de autenticação
masterdeck_blueprint = Blueprint('masterdecks_blueprint', __name__)

# Definindo as rotas
masterdeck_blueprint.route('/create', methods=['POST'])(MasterDecksController.createMasterDeck)
masterdeck_blueprint.route('/get', methods=['GET'])(MasterDecksController.get_all_masterdecks)
masterdeck_blueprint.route('/get_by_user', methods=['GET'])(MasterDecksController.get_masterdecks_by_user)
masterdeck_blueprint.route('/get/<string:deck_id>', methods=['GET'])(MasterDecksController.get_by_id)
masterdeck_blueprint.route('/add_decks/<string:masterdeck_id>', methods=['PATCH'])(MasterDecksController.add_decks_to_masterdeck)