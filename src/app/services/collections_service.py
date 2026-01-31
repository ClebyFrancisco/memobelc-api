# src/app/services/deck_service.py

from bson import ObjectId
from src.app import mongo
from src.app.models.collection_model import CollectionModel
from src.app.models.deck_model import DeckModel
from src.app.models.card_model import CardModel
from src.app.models.classroom_model import ClassroomModel


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
    def get_collections_by_user(user_id, include_book_collections_for_admin=False):
        """Retorna collections do usuário. Se admin, inclui também as collections dos livros."""
        return CollectionModel.get_collections_by_user(
            user_id, include_book_collections_for_admin=include_book_collections_for_admin
        )

    @staticmethod
    def get_all_collections():
        return CollectionModel.get_all_collections()

    @staticmethod
    def add_decks_to_collection(collection_id, deck_ids):
        return CollectionModel.add_decks_to_collection(collection_id, deck_ids)
    
    @staticmethod
    def update_collection(collection_id, name=None, image=None):
        """Atualiza os dados de uma collection"""
        return CollectionModel.update_collection(collection_id, name=name, image=image)

    @staticmethod
    def delete_collection(collection_id):
        """Deleta uma collection e todos os recursos dependentes.
        
        A lógica de deleção em cascata:
        0. Se a collection estiver vinculada a uma classroom, não deve ser apagada
        1. Deleta decks que pertencem APENAS a esta collection
        2. Para cada deck deletado, deleta cards que pertencem APENAS aquele deck
        3. Deleta user_progress relacionados aos cards/decks deletados
        4. Deleta a collection
        
        Args:
            collection_id: ID da collection a ser deletada
            
        Returns:
            bool: True se a collection foi deletada, False caso contrário
        """
        # Buscar a collection
        collection = CollectionModel.get_by_id(collection_id)
        if not collection:
            return False

        # 0. Se a collection estiver sendo usada em uma classroom, não apagar
        if collection.get("classroom"):
            return False

        # 0b. Se a collection for a collection de um livro (book.collection_id), não apagar por aqui
        # (deve ser removida ao deletar o livro)
        collection_obj_id = ObjectId(collection_id)
        if mongo.db.books.find_one({"collection_id": collection_obj_id}):
            return False
        decks_to_delete = []
        cards_to_delete = []
        
        # 1. Identificar decks que pertencem APENAS a esta collection
        deck_ids = collection.get("decks", [])
        for deck_id in deck_ids:
            deck_obj_id = ObjectId(deck_id) if not isinstance(deck_id, ObjectId) else deck_id
            
            # Verificar quantas collections têm este deck
            collections_with_deck = mongo.db.collections.count_documents({
                "decks": deck_obj_id
            })
            
            # Se o deck pertence apenas a esta collection, marcar para deletar
            if collections_with_deck == 1:
                decks_to_delete.append(deck_obj_id)
        
        # 2. Para cada deck a ser deletado, identificar cards que pertencem APENAS a ele
        for deck_id in decks_to_delete:
            deck = DeckModel.get_by_id(str(deck_id))
            if not deck:
                continue
            
            card_ids = deck.get("cards", [])
            for card_id in card_ids:
                card_obj_id = ObjectId(card_id) if not isinstance(card_id, ObjectId) else card_id
                
                # Verificar quantos decks têm este card
                decks_with_card = mongo.db.decks.count_documents({
                    "cards": card_obj_id
                })
                
                # Se o card pertence apenas a este deck, marcar para deletar
                if decks_with_card == 1:
                    cards_to_delete.append((str(deck_id), card_obj_id))
        
        # 3. Deletar user_progress dos cards que serão deletados
        for deck_id_str, card_obj_id in cards_to_delete:
            mongo.db.user_progress.delete_many({
                "deck_id": ObjectId(deck_id_str),
                "card_id": card_obj_id
            })
        
        # 4. Deletar os cards marcados
        for deck_id_str, card_obj_id in cards_to_delete:
            mongo.db.cards.delete_one({"_id": card_obj_id})
        
        # 5. Deletar os decks marcados
        for deck_id in decks_to_delete:
            mongo.db.decks.delete_one({"_id": deck_id})

        # 6. Remover a collection da lista de collections de todos os usuários
        mongo.db.users.update_many(
            {"collections": collection_obj_id},
            {"$pull": {"collections": collection_obj_id}}
        )
        
        # 7. Deletar a collection
        result = mongo.db.collections.delete_one({"_id": collection_obj_id})
        
        return result.deleted_count > 0
