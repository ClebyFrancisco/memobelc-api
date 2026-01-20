from src.app.models.card_model import CardModel
from datetime import datetime, timezone

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
        if card:
            card.delete_from_db()
            return True
        return False
