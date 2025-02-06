import random
from bson import ObjectId
from datetime import datetime, timedelta
from src.app import mongo
from .user_model import UserModel
from .user_progress_model import UserProgressModel


class CollectionModel:
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
        result = mongo.db.collections.insert_one(deck_data)
        self.id = str(result.inserted_id)

        if self.user:
            UserModel.add_collections_to_user(self.user, [str(result.inserted_id)])

        return True
    
    @staticmethod
    def get_all_collections():
        """Retorna todos os collections como uma lista de dicionários"""
        collections = mongo.db.collections.find()
        return [CollectionModel.to_dict(collection) for collection in collections]
    
    @staticmethod
    def get_by_id(deck_id):
        """Busca um Collection pelo ID e retorna como dicionário"""
        collection = mongo.db.collections.find_one({"_id": ObjectId(deck_id)})
        if collection:
            result = CollectionModel(**collection)
            return result.to_dict()
        return None
    

    @staticmethod
    def get_collections_by_user(user_id):
        """"Busca todos os master decks do user e retorna a quantidade de cartas totais e pendentes."""
        user = UserModel.find_by_id(user_id)
        
        
        user = user.to_dict()

        collections_list = []
    
        for collection_id in user.get("collections", []):
            collection = CollectionModel.get_by_id(collection_id)

            total_cards = 0
            pending_cards = 0
            
            
            
            from .deck_model import DeckModel

            # Percorre cada deck associado ao collection
            for deck_id in collection.get("decks", []):
                deck = DeckModel.get_by_id(deck_id)

                # Conta o número total de cartas no deck
                cards_count =  len(deck.get("cards", []))
                total_cards += cards_count

                # Conta o número de cartas pendentes no UserProgressModel
                pending_count = UserProgressModel.count_pending_cards(user_id, deck_id)
                pending_cards += pending_count

            # Adiciona contagens ao dicionário de dados do collection
            collection.update({
                "total_cards": total_cards,
                "pending_cards": pending_cards
            })
            
             # Adiciona collection à lista final
            collections_list.append(collection)

        return {
            "collections":collections_list
            }
    

    @staticmethod
    def add_decks_to_collection(collection_id, deck_ids):
        """Adiciona uma lista de deck IDs ao Collection especificado"""
        # Converte os IDs de decks para ObjectId
        deck_object_ids = [ObjectId(deck_id) for deck_id in deck_ids]
        
        # Atualiza o Collection, adicionando os IDs dos decks
        result = mongo.db.collections.update_one(
            {"_id": ObjectId(collection_id)},
            {"$push": {"decks": {"$each": deck_object_ids}}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    

    def to_dict(self):
        """Converte um documento collection para dicionário"""
        return {
            '_id': self.id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'image': self.image,
            'decks': [str(ObjectId(deck_id)) for deck_id in self.decks]
        }

