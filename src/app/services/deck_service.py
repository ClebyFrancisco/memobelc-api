# src/app/services/deck_service.py

from src.app.models.deck_model import DeckModel


class DeckService:
    @staticmethod
    def create_deck(name, collection_id, image=None):
        """Cria um novo mastdeck e o salva no banco de dados"""

        deck = DeckModel(name=name, collection_id=collection_id, image=image)
        deck.save_to_db()
        return "Ok"

    @staticmethod
    def get_all_decks():
        return DeckModel.get_all_decks()

    @staticmethod
    def get_decks_by_collection_id(collection_id, user_id):
        """This method returns all deck in collection"""

        return DeckModel.get_decks_by_collection_id(collection_id, user_id)
    
    @staticmethod
    def save_deck(user_id, deck_id, collection_id):
        """This method is responsible for save deck in user"""
    
        return DeckModel.save_deck(user_id, deck_id, collection_id)
    
    @staticmethod
    def check_if_the_user_has_the_deck(user_id, deck_id):
        """This method is responsible for verify if the deck has the user"""
        
        return DeckModel.check_if_the_user_has_the_deck(user_id, deck_id)
