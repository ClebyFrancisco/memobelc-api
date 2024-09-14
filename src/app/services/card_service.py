from ..models.card_model import CardModel

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
    def update_card(card_id, front=None, back=None):
        """Atualiza um cartão existente"""
        card = CardModel.find_by_id(card_id)
        if card:
            if front:
                card.front = front
            if back:
                card.back = back
            card.updated_at = datetime.utcnow()
            card.save_to_db()
        return card

    @staticmethod
    def delete_card(card_id):
        """Remove um cartão pelo ID"""
        mongo.db.cards.delete_one({'_id': card_id})