from src.app.models.card_model import CardModel
from src.app.models.deck_model import DeckModel
from datetime import datetime, timezone
from bson import ObjectId
from src.app import mongo

from src.app.services.notification_service import NotificationService


class CardService:
    @staticmethod
    def create_card(front, back, deck_id=None, user=None, audio=None, media_type='text'):
        """Cria um novo card e o salva no banco de dados."""
        card = CardModel(
            front=front,
            back=back,
            deck=deck_id,
            user=user,
            audio=audio,
            media_type=media_type,
        )
        card.save_to_db()
        card_dict = card.to_dict()

        # notifica alunos de classrooms vinculadas a este deck
        if deck_id:
            NotificationService.notify_students_new_cards(deck_id=str(deck_id), amount=1)

        return card_dict

    @staticmethod
    def get_card_by_id(card_id):
        """Busca um card pelo ID e o retorna como dicionário."""
        card = CardModel.get_by_id(card_id)
        return card.to_dict() if card else None
    
    @staticmethod
    def create_card_in_lots(name, image, cards):
        deck_id = CardModel.create_card_in_lots(name, image, cards)

        # notifica alunos que há novas cartas neste deck
        if deck_id and isinstance(deck_id, str):
            NotificationService.notify_students_new_cards(deck_id=deck_id, amount=len(cards))

        return "ok"
    
    @staticmethod
    def get_cards_by_deck(deck_id):
        """This method is responsible for get all cards in deck"""
        
        return CardModel.get_cards_by_deck(deck_id)

    @staticmethod
    def get_all_cards():
        """Retorna todos os cards como uma lista de dicionários."""
        cards = CardModel.get_all_cards()
        return [card.to_dict() for card in cards]

    @staticmethod
    def update_card(card_id, data):
        """Atualiza os dados de um card existente."""
        card = CardModel.get_by_id(card_id)
        if not card:
            return None
        if isinstance(card, dict):
            card = CardModel(**card)

        card.front = data.get("front", card.front)
        card.back = data.get("back", card.back)
        card.media_type = data.get("media_type", card.media_type)
        card.updated_at = datetime.now(timezone.utc)

        card.save_to_db()
        return card.to_dict()

    @staticmethod
    def delete_card(card_id):
        """Exclui um card pelo ID."""
        card = CardModel.get_by_id(card_id)
        if not card:
            return False
        if isinstance(card, dict):
            card = CardModel(**card)
        card.delete_from_db()
        return True

    @staticmethod
    def check_card_permission(card_id, user_id, user_role):
        """
        Verifica se o usuário tem permissão para editar/excluir um card.
        Retorna um dict com: {"can_edit": bool, "reason": str}
        """
        # Admin pode editar tudo
        if user_role == "admin":
            return {"can_edit": True, "reason": "admin"}
        
        # Busca o card
        card = CardModel.get_by_id(card_id)
        if not card:
            return {"can_edit": False, "reason": "card_not_found"}
        
        if isinstance(card, dict):
            card_dict = card
        else:
            card_dict = card.to_dict()
        
        deck_id = card_dict.get("deck")
        if not deck_id:
            return {"can_edit": False, "reason": "no_deck"}
        
        # Busca o deck
        deck = DeckModel.get_by_id(deck_id)
        if not deck:
            return {"can_edit": False, "reason": "deck_not_found"}
        
        if isinstance(deck, dict):
            deck_dict = deck
        else:
            deck_dict = deck.to_dict()
        
        collection_id = deck_dict.get("collection")
        if not collection_id:
            return {"can_edit": False, "reason": "no_collection"}
        
        # Busca a collection
        collection = mongo.db.collections.find_one({"_id": ObjectId(collection_id)})
        if not collection:
            return {"can_edit": False, "reason": "collection_not_found"}
        
        # Verifica se é uma collection de livro
        if collection.get("book_id"):
            return {"can_edit": False, "reason": "book_collection_only_admin"}
        
        # Verifica se é uma collection de classroom
        if collection.get("classroom"):
            classroom = mongo.db.classrooms.find_one({"_id": ObjectId(collection.get("classroom"))})
            if classroom:
                teacher_id = str(classroom.get("teacher"))
                if teacher_id == user_id:
                    return {"can_edit": True, "reason": "classroom_teacher"}
                else:
                    return {"can_edit": False, "reason": "not_classroom_teacher"}
        
        # Collection pessoal - verifica se o usuário é dono
        collection_user_id = str(collection.get("user"))
        if collection_user_id == user_id:
            return {"can_edit": True, "reason": "personal_collection_owner"}
        
        return {"can_edit": False, "reason": "no_permission"}

