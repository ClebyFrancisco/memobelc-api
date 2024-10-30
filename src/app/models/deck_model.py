import random
from bson import ObjectId
from datetime import datetime, timedelta
from src.app import mongo

class DeckModel:
    def __init__(self, _id=None, name=None, created_at=None, updated_at=None, image=None, decks=None):
        self.id = str(_id) if _id else None
        self.name = name
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.image = image
        self.decks = decks or []

    def save_to_db(self):
        """Salva o  deck no banco de dados MongoDB"""
        deck_data = {
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'image': self.image,
            'decks': self.decks
        }
        result = mongo.db. decks.insert_one(deck_data)
        self.id = str(result.inserted_id)
        return True
    
    @staticmethod
    def get_all_decks():
        """Retorna todos os  decks como uma lista de dicionários"""
        decks = mongo.db. decks.find()
        return [ DeckModel.to_dict( deck) for  deck in  decks]
    
    @staticmethod
    def to_dict( deck):
        """Converte um documento  deck para dicionário"""
        return {
            '_id': str( deck.get('_id')),
            'name':  deck.get('name'),
            'created_at':  deck.get('created_at'),
            'updated_at':  deck.get('updated_at'),
            'image':  deck.get('image'),
            'decks':  deck.get('decks', [])
        }
