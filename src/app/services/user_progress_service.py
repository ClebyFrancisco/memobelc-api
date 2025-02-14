from datetime import datetime
from src.app.models.user_progress_model import UserProgressModel


class UserProgressService:

    @staticmethod
    def create_or_update_progress(user_id, deck_id, card_id):
        """Cria ou atualiza o progresso do usuário para uma carta específica."""
        UserProgressModel.create_or_update(user_id, deck_id, card_id)

    @staticmethod
    def get_pending_cards(user_id, deck_id=None):
        """Obtém todas as cartas pendentes para revisão no dia atual."""
        return UserProgressModel.get_pending_cards(user_id, deck_id)

    @staticmethod
    def update_card_status(user_id, card_id, recall_level):
        """Atualiza o status de uma carta específica no progresso do usuário."""
        progress = UserProgressModel.update_status(user_id, card_id, recall_level)
        return progress

    @staticmethod
    def get_progress_for_card(user_id, deck_id, card_id):
        """Recupera o progresso de um usuário para uma carta específica."""
        progress_data = UserProgressModel.get_progress(user_id, deck_id, card_id)
        return progress_data if progress_data else None
