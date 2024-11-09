# src/app/services/deck_service.py

from app.models.deck_model import DeckModel


class DeckService:
    @staticmethod
    def create_deck(name, masterdeck_id, image=None):
        """Cria um novo mastdeck e o salva no banco de dados"""
        deck = DeckModel(name=name, masterdeck_id=masterdeck_id, image=image)
        deck.save_to_db()
        return "Ok"

    @staticmethod
    def get_all_decks():
        return DeckModel.get_all_decks()
