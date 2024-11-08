import random
from bson import ObjectId
from datetime import datetime, timedelta
from src.app import mongo
from .user_model import UserModel
from .user_progress_model import UserProgressModel


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
            UserModel.add_masterdecks_to_user(self.user, [str(result.inserted_id)])

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
        if masterdeck:
            result = MasterDeckModel(**masterdeck)
            return result.to_dict()
        return None
    

    @staticmethod
    def get_masterdecks_by_user(user_id):
        """"Busca todos os master decks do user e retorna a quantidade de cartas totais e pendentes."""
        user = UserModel.find_by_id(user_id)
        
        
        user = user.to_dict()

        masterdecks_list = []
    
        for masterdeck_id in user.get("masterdecks", []):
            masterdeck = MasterDeckModel.get_by_id(masterdeck_id)

            total_cards = 0
            pending_cards = 0
            
            
            
            from .deck_model import DeckModel

            # Percorre cada deck associado ao masterdeck
            for deck_id in masterdeck.get("decks", []):
                deck = DeckModel.get_by_id(deck_id)

                # Conta o número total de cartas no deck
                cards_count =  len(deck.get("cards", []))
                total_cards += cards_count

                # Conta o número de cartas pendentes no UserProgressModel
                pending_count = UserProgressModel.count_pending_cards(user_id, deck_id)
                pending_cards += pending_count

            # Adiciona contagens ao dicionário de dados do masterdeck
            masterdeck.update({
                "total_cards": total_cards,
                "pending_cards": pending_cards
            })
            
             # Adiciona masterdeck à lista final
            masterdecks_list.append(masterdeck)

        return {
            "masterdecks":masterdecks_list
            }
    

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
    

    def to_dict(self):
        """Converte um documento masterdeck para dicionário"""
        return {
            '_id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'image': self.image,
            'decks': [str(ObjectId(deck_id)) for deck_id in self.decks]
        }

