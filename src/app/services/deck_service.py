# src/app/services/deck_service.py

from ..models.deck_model import DeckModel
from ..models.card_model import CardModel

class DeckService:
    @staticmethod
    def create_deck(name, image=None):
        """Cria um novo deck e o salva no banco de dados"""
        deck = DeckModel(name=name, image=image)
        deck.save_to_db()
        return deck

    @staticmethod
    def get_deck_by_id(deck_id):
        """Busca um deck pelo ID"""
        return DeckModel.find_by_id(deck_id)

    @staticmethod
    def update_deck(deck_id, name=None, image=None):
        """Atualiza um deck existente"""
        deck = DeckModel.find_by_id(deck_id)
        if deck:
            if name:
                deck.name = name
            if image:
                deck.image = image
            deck.updated_at = datetime.utcnow()
            deck.save_to_db()
        return deck

    @staticmethod
    def delete_deck(deck_id):
        """Remove um deck pelo ID"""
        mongo.db.decks.delete_one({'_id': deck_id})

    @staticmethod
    def add_card_to_deck(deck_id, card_id):
        """Adiciona um cartão ao deck"""
        deck = DeckModel.find_by_id(deck_id)
        if deck:
            card = CardModel.find_by_id(card_id)
            if card:
                deck.add_card(card)

    @staticmethod
    def remove_card_from_deck(deck_id, card_id):
        """Remove um cartão do deck"""
        deck = DeckModel.find_by_id(deck_id)
        if deck:
            deck.remove_card(card_id)
