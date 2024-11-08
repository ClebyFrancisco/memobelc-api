import random
from bson import ObjectId
from datetime import datetime, timedelta
from src.app import mongo
from .masterdeck_model import MasterDeckModel

class DeckModel:
    def __init__(self, _id=None, name=None, created_at=None, updated_at=None, masterdeck_id=None, image=None,cards=None):
        self.id = str(_id) if _id else None
        self.name = name
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.masterdeck_id = masterdeck_id
        self.image = image
        self.cards = cards or []
        
    @staticmethod
    def get_by_id(deck_id):
        """Busca um Deck pelo ID e retorna como dicionário"""
        deck = mongo.db.decks.find_one({"_id": ObjectId(deck_id)})
        if deck:
            result = DeckModel(**deck)
            return result.to_dict()
        return None

    def save_to_db(self):
        """Salva o  deck no banco de dados MongoDB"""
        deck_data = {
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'image': self.image,
            'cards': self.cards
        }
        result = mongo.db. decks.insert_one(deck_data)
        self.id = str(result.inserted_id)
        if self.masterdeck_id:
                MasterDeckModel.add_decks_to_masterdeck(self.masterdeck_id, [str(result.inserted_id)])
        return True
    
    @staticmethod
    def get_all_decks():
        """Retorna todos os  decks como uma lista de dicionários"""
        decks = mongo.db. decks.find()
        return [ DeckModel.to_dict( deck) for  deck in  decks]
    
    @staticmethod
    def add_cards_to_deck(deck_id, cards_ids):
        """Adiciona uma lista de cards IDs ao deck especificado"""
        # Converte os IDs de decks para ObjectId
        cards_object_ids = [ObjectId(card_id) for card_id in cards_ids]
        
        # Atualiza o MasterDeck, adicionando os IDs dos decks
        result = mongo.db.decks.update_one(
            {"_id": ObjectId(deck_id)},
            {"$push": {"cards": {"$each": cards_object_ids}}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
    def to_dict(self):
        """Converte um documento deck para dicionário"""
        return {
            '_id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'image': self.image,
            'cards': [str(ObjectId(card_id)) for card_id in self.cards]
        }
