import random
from bson import ObjectId
from werkzeug.exceptions import BadRequest
from datetime import datetime, timedelta, timezone
from src.app import mongo
from .collection_model import CollectionModel
from .user_model import UserModel
from .user_progress_model import UserProgressModel


class DeckModel:
    def __init__(
        self,
        _id=None,
        name=None,
        created_at=None,
        updated_at=None,
        collection_id=None,
        image=None,
        cards=None,
    ):
        self.id = str(_id) if _id else None
        self.name = name
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.collection_id = collection_id
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
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "image": self.image,
            "cards": self.cards,
        }
        result = mongo.db.decks.insert_one(deck_data)
        self.id = str(result.inserted_id)
        if self.collection_id:
            CollectionModel.add_decks_to_collection(
                self.collection_id, [str(result.inserted_id)]
            )
        return str(result.inserted_id)

    @staticmethod
    def get_all_decks():
        """Retorna todos os  decks como uma lista de dicionários"""
        decks = mongo.db.decks.find()
        return [DeckModel.to_dict(deck) for deck in decks]

    @staticmethod
    def add_cards_to_deck(deck_id, cards_ids):
        """Adiciona uma lista de cards IDs ao deck especificado"""
        # Converte os IDs de decks para ObjectId
        cards_object_ids = [ObjectId(card_id) for card_id in cards_ids]

        # Atualiza o Collection, adicionando os IDs dos decks
        result = mongo.db.decks.update_one(
            {"_id": ObjectId(deck_id)},
            {
                "$push": {"cards": {"$each": cards_object_ids}},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )

        return result.modified_count > 0

    @staticmethod
    def get_decks_by_collection_id(collection_id, user_id):
        """ "Busca todos os decks do user e retorna a quantidade de cartas totais e pendentes."""
        collection = CollectionModel.get_by_id(collection_id)

        decks_list = []

        for deck_id in collection.get("decks", []):
            deck = DeckModel.get_by_id(deck_id)

            pending_count = UserProgressModel.count_pending_cards(
                user_id, deck.get("id")
            )

            deck.update(
                {
                    "total_cards": len(deck.get("cards", [])),
                    "pending_cards": pending_count,
                }
            )

            from .card_model import CardModel

            cards_list = []

            for card_id in deck.get("cards", []):
                card = CardModel.get_by_id(card_id)

                cards_list.append(card)

            deck.update(
                {
                    "cards": cards_list,
                }
            )
            decks_list.append(deck)

        return {"decks": decks_list}
    
    @staticmethod
    def save_deck(user_id, deck_id, collection_id):
        deck = DeckModel.get_by_id(deck_id)
        
        if(deck):
            CollectionModel.add_decks_to_collection(
                    collection_id, [deck.get("_id")]
                )
        else:
            return


        for card_id in deck.get("cards", []):
            UserProgressModel.create_or_update(user_id, deck_id, card_id)
            
        return True
    
    @staticmethod
    def check_if_the_user_has_the_deck(user_id, deck_id):
        user = UserModel.find_by_id(user_id)
        user = user.to_dict()
        
        if not user:
            return BadRequest(description="error: user not found!")

        for collection_id in user.get("collections", []):
            collection = CollectionModel.get_by_id(collection_id)
            
            if not collection:
                continue  

            if deck_id in collection.get("decks", []):
                return {"user_has_deck": "true"}

        return {"user_has_deck": "false"} 
    
    

    def to_dict(self):
        """Converte um documento deck para dicionário"""
        return {
            "_id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "image": self.image,
            "cards": [str(ObjectId(card_id)) for card_id in self.cards],
        }
