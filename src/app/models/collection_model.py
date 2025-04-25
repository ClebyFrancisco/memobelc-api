import random
from bson import ObjectId
from datetime import datetime, timedelta, timezone
from src.app import mongo
from .user_model import UserModel
from .user_progress_model import UserProgressModel


class CollectionModel:
    def __init__(self, _id=None, name=None, created_at=None, updated_at=None, image=None, decks=None, user=None, classroom=None):
        self._id = str(_id) if _id else None
        self.name = name
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.image = image
        self.decks = decks or []
        self.user = user
        self.classroom = classroom

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

        return {"collection_id": str(result.inserted_id)}
    
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
    def add_classroom(classroom_id, collection_id):
        mongo.db.collections.update_one(
            {"_id": ObjectId(collection_id)},
            {"$set": {"classroom": ObjectId(classroom_id)}}
        )

    

    @staticmethod
    def get_collections_by_user(user_id):
        """"Busca todos os master decks do user e retorna a quantidade de cartas totais e pendentes."""
        user = UserModel.find_by_id(user_id)
        
        
        user = user.to_dict()

        collections_list = []
        
    
        for collection_id in user.get("collections", []):
            collection = CollectionModel.get_by_id(collection_id)

            total_cards_in_collection = 0
            pending_cards_in_collection = 0

            list_deck_in_collection = []
            review_collections_cards = []
            
            
            
            from .deck_model import DeckModel

            
            for deck_id in collection.get("decks", []):
                deck = DeckModel.get_by_id(deck_id)



                
                cards_count =  len(deck.get("cards", []))
                total_cards_in_collection += cards_count

                
                pending_count = UserProgressModel.count_pending_cards(user_id, deck_id)
                pending_cards_in_collection += pending_count
                
                
                review_cards = UserProgressModel.get_pending_cards(user_id, deck_id)
                
                for card in review_cards:
                    review_collections_cards.append(card)

                deck.update({
                    "total_cards": cards_count,
                    "pending_cards": pending_count,
                    "review_cards": review_cards

                })
                

                list_deck_in_collection.append(deck)

            
            collection.update({
                "total_cards": total_cards_in_collection,
                "pending_cards": pending_cards_in_collection,
                "decks": list_deck_in_collection,
                "review_collections_cards": review_collections_cards
            })
            
            
            collections_list.append(collection)

        return {
            "collections":collections_list
            }
    

    @staticmethod
    def add_decks_to_collection(collection_id, deck_ids):
        """Adiciona uma lista de deck IDs ao Collection especificado"""
        
        deck_object_ids = [ObjectId(deck_id) for deck_id in deck_ids]
        
        
        result = mongo.db.collections.update_one(
            {"_id": ObjectId(collection_id)},
            {"$push": {"decks": {"$each": deck_object_ids}}, "$set": {"updated_at": datetime.now(timezone.utc)}}
        )
        
        return result.modified_count > 0
    

    def to_dict(self):
        """Converte um documento collection para dicionário"""
        return {
            '_id': self._id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'image': self.image,
            'decks': [str(ObjectId(deck_id)) for deck_id in self.decks],
            'classroom':str(self.classroom) if self.classroom else self.classroom
        }

