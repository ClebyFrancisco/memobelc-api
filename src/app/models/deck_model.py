import random
from bson import ObjectId
from datetime import datetime, timedelta
from src.app import mongo

class DeckModel:
    def __init__(self, _id=None, name=None, created_at=None, updated_at=None, image=None, cards=None):
        self.id = str(_id) if _id else None
        self.name = name
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.image = image
        self.cards = cards or []

    def save_to_db(self):
        """Salva o deck no banco de dados MongoDB"""
        deck_data = {
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'image': self.image,
            'cards': self.cards
        }
        result = mongo.db.decks.insert_one(deck_data)
        self.id = str(result.inserted_id)
        return self

    def get_next_cards(self, limit=10):
        """Seleciona as próximas cartas para o usuário com base no desempenho"""
        deck_data = mongo.db.decks.find_one({'_id': ObjectId(self.id)})
        card_ids = deck_data.get('cards', [])
        cards = [CardModel.find_by_id(card_id) for card_id in card_ids]

        # Prioriza cartas com mais erros e menor fator de facilidade
        cards.sort(key=lambda card: (card.ease_factor, card.mistakes, card.last_viewed_at))

        # Seleciona as cartas menos vistas recentemente
        cards = [card for card in cards if card.last_viewed_at <= datetime.utcnow() - timedelta(days=1)]

        return random.sample(cards, min(limit, len(cards)))

    def add_card(self, card_id):
        """Adiciona um card ao deck"""
        self.cards.append(card_id)
        mongo.db.decks.update_one(
            {'_id': ObjectId(self.id)},
            {'$set': {'cards': self.cards}}
        )
    
    def to_dict(self):
        """Converte o objeto DeckModel para dicionário"""
        return {
            '_id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'image': self.image,
            'cards': self.cards
        }
