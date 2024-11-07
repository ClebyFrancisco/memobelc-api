import random
from bson import ObjectId
from datetime import datetime, timedelta
from src.app import mongo
from .user_model import UserModel

class MasterDeckModel:
    def __init__(self, _id=None, name=None, created_at=None, updated_at=None, image=None, decks=None, user=None):
        self.id = str(_id) if _id else None
        self.name = name
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.image = image
        self.decks = decks or []
        self.user = user

    def save_to_db(self):
        """Salva o Masterdeck no banco de dados MongoDB"""
        deck_data = {
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'image': self.image,
            'decks': self.decks
        }
        result = mongo.db.masterdecks.insert_one(deck_data)
        self.id = str(result.inserted_id)

        if self.user:
            UserModel.add_masterdecks_to_user(self.user, [self.id])

        return True
    
    @staticmethod
    def get_all_masterdecks():
        """Retorna todos os masterdecks como uma lista de dicionários"""
        masterdecks = mongo.db.masterdecks.find()
        return [MasterDeckModel.to_dict(masterdeck) for masterdeck in masterdecks]
    
    @staticmethod
    def get_by_id(deck_id):
        """Busca um MasterDeck pelo ID e retorna como dicionário"""
        masterdeck = mongo.db.masterdecks.find_one({"_id": ObjectId(deck_id)})
        return MasterDeckModel.to_dict(masterdeck) if masterdeck else None
    

    @staticmethod
    def add_decks_to_masterdeck(masterdeck_id, deck_ids):
        """Adiciona uma lista de deck IDs ao MasterDeck especificado"""
        # Converte os IDs de decks para ObjectId
        deck_object_ids = [ObjectId(deck_id) for deck_id in deck_ids]
        
        # Atualiza o MasterDeck, adicionando os IDs dos decks
        result = mongo.db.masterdecks.update_one(
            {"_id": ObjectId(masterdeck_id)},
            {"$push": {"decks": {"$each": deck_object_ids}}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
    @staticmethod
    def to_dict(masterdeck):
        """Converte um documento masterdeck para dicionário"""
        return {
            '_id': str(masterdeck.get('_id')),
            'name': masterdeck.get('name'),
            'created_at': masterdeck.get('created_at'),
            'updated_at': masterdeck.get('updated_at'),
            'image': masterdeck.get('image'),
            'decks': [str(deck_id) for deck_id in masterdeck.get('decks', [])]
        }
