# src/app/services/deck_service.py

from src.app.models.collection_model import CollectionModel


class CollectionService:
    @staticmethod
    def create_collection(name, image=None, user=None):
        """Cria um novo mastdeck e o salva no banco de dados"""
        deck = CollectionModel(name=name, image=image, user=user)
        result = deck.save_to_db()
        return result

    @staticmethod
    def get_by_id(deck_id):
        """Busca um Collection pelo ID"""
        collection = CollectionModel.get_by_id(deck_id)
        return collection

    @staticmethod
    def get_collections_by_user(user_id):
        return CollectionModel.get_collections_by_user(user_id)

    @staticmethod
    def get_all_collections():
        return CollectionModel.get_all_collections()

    @staticmethod
    def add_decks_to_collection(collection_id, deck_ids):
        return CollectionModel.add_decks_to_collection(collection_id, deck_ids)
