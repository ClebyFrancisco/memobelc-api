from datetime import datetime
from bson import ObjectId
from src.app import mongo

class CardModel:
    def __init__(self, _id=None, front=None, back=None, created_at=None, updated_at=None, total_views=0, mistakes=0, last_viewed_at=None, ease_factor=2.5):
        self._id = str(_id) if _id else None
        self.front = front
        self.back = back
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.total_views = total_views
        self.mistakes = mistakes
        self.last_viewed_at = last_viewed_at or datetime.utcnow()
        self.ease_factor = ease_factor  # Facilitate the appearance rate (lower = harder to remember)

    def save_to_db(self):
        """Salva o cartão no banco de dados MongoDB"""
        card_data = {
            'front': self.front,
            'back': self.back,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'total_views': self.total_views,
            'mistakes': self.mistakes,
            'last_viewed_at': self.last_viewed_at,
            'ease_factor': self.ease_factor
        }
        result = mongo.db.cards.insert_one(card_data)
        self.id = str(result.inserted_id)
        return self

    def update_performance(self, success):
        """Atualiza o desempenho do card baseado na resposta do usuário"""
        self.total_views += 1
        if not success:
            self.mistakes += 1
            self.ease_factor = max(1.3, self.ease_factor - 0.15)  # Diminui o fator de facilidade
        else:
            self.ease_factor = min(2.5, self.ease_factor + 0.1)  # Aumenta o fator de facilidade
        
        self.last_viewed_at = datetime.utcnow()
        mongo.db.cards.update_one(
            {'_id': ObjectId(self.id)},
            {'$set': {
                'total_views': self.total_views,
                'mistakes': self.mistakes,
                'ease_factor': self.ease_factor,
                'last_viewed_at': self.last_viewed_at
            }}
        )

    @staticmethod
    def get_card_by_id(card_id):
        """Busca um card pelo ID"""
        card_data = mongo.db.cards.find_one({'_id': ObjectId(card_id)})
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
            'updated_at': self.updated_at,
            'total_views': self.total_views,
            'mistakes': self.mistakes,
            'last_viewed_at': self.last_viewed_at,
            'ease_factor': self.ease_factor
        }
        
    def delete_card(card_id):
        """Deleta um card"""
        result = mongo.db.cards.delete_one({'_id': ObjectId(card_id)})
        return result.deleted_count > 0
