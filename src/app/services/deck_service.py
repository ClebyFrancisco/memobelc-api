# src/app/services/deck_service.py

from src.app.models.deck_model import DeckModel
from src.app.models.card_model import CardModel
from src.app.models.user_progress_model import UserProgressModel


class DeckService:
    @staticmethod
    def create_deck(name, collection_id, image=None, cards=None):
        """Cria um novo deck e o salva no banco de dados"""

        deck = DeckModel(name=name, collection_id=collection_id, image=image)
        deck_id = deck.save_to_db()

        if cards is not None:
            card_ids = []
            for card in cards:
                card_data = CardModel(**card)
                card_id = card_data.save_to_db()
                card_ids.append(card_id)

            DeckModel.add_cards_to_deck(deck_id, card_ids)

            users = CardModel.get_user_by_deck(deck_id)

            for user_id in users:
                for card_id in card_ids:
                    UserProgressModel.create_or_update(user_id, deck_id, card_id)

        return {"message": "Deck criado com sucesso", "deck_id": deck_id}


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
