from src.app import mongo
from datetime import datetime

class CardModel:
    def __init__(self, _id=None, front=None, back=None, created_at=None, updated_at=None):
        self.id = str(_id)
        self.front = front  # front pode ser um dicionário contendo tipo e conteúdo
        self.back = back    # back pode ser um dicionário contendo tipo e conteúdo
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def save_to_db(self):
        """Salva o cartão no banco de dados MongoDB"""
        card_data = self.to_dict()
        if self.id:
            mongo.db.cards.update_one({'_id': self.id}, {'$set': card_data}, upsert=True)
        else:
            result = mongo.db.cards.insert_one(card_data)
            self.id = str(result.inserted_id)

    @staticmethod
    def find_by_id(card_id):
        """Busca um cartão pelo ID"""
        card_data = mongo.db.cards.find_one({'_id': card_id})
        if card_data:
            return CardModel(**card_data)
        return None

    def to_dict(self):
        """Converte o objeto CardModel para dicionário"""
        return {
            '_id': self.id,
            'front': self.front,
            'back': self.back,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }