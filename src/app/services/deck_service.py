# src/app/services/deck_service.py

from ..models.deck_model import DeckModel

class DeckService:
    @staticmethod
    def create_deck(name, image=None):
        """Cria um novo mastdeck e o salva no banco de dados"""
        deck = DeckModel(name=name, image=image)
        deck.save_to_db()
        return "Ok"

    @staticmethod
    def get_all_decks():
        return DeckModel.get_all_decks()


