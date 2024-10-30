# src/app/services/deck_service.py

from ..models.masterdeck_model import MasterDeckModel

class MasterDeckService:
    @staticmethod
    def create_masterdeck(name, image=None):
        """Cria um novo mastdeck e o salva no banco de dados"""
        deck = MasterDeckModel(name=name, image=image)
        deck.save_to_db()
        return "Ok"
    
    @staticmethod
    def get_by_id(deck_id):
        """Busca um MasterDeck pelo ID"""
        masterdeck = MasterDeckModel.get_by_id(deck_id)
        return masterdeck

    @staticmethod
    def get_all_masterdecks():
        return MasterDeckModel.get_all_masterdecks()
    

    @staticmethod
    def add_decks_to_masterdeck(masterdeck_id, deck_ids):
        return MasterDeckModel.add_decks_to_masterdeck(masterdeck_id, deck_ids)

