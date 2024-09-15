from ..models.card_model import CardModel
from bson import ObjectId

class CardService:
    @staticmethod
    def create_card(front, back):
        """Cria um novo cartão e o salva no banco de dados"""
        card = CardModel(front=front, back=back)
        card.save_to_db()
        return card

    @staticmethod
    def get_card_by_id(card_id):
        """Busca um cartão pelo ID"""
        return CardModel.find_by_id(card_id)

    @staticmethod
    def update_card_performance(card_id, success):
        """Atualiza o desempenho de um card"""
        card = CardService.get_card_by_id(card_id)
        if card:
            card.update_performance(success)
            return card
        return None

    @staticmethod
    def delete_card(card_id):
        return CardModel.delete_card(card_id)   
