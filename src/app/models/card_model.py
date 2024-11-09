"""Model class for cards"""

from datetime import datetime
from bson import ObjectId
from src.app import mongo
from app.models.deck_model import DeckModel
from app.models.user_progress_model import UserProgressModel


class CardModel:
    """Class to handle model cards"""

    def __init__(
        self,
        _id=None,
        front=None,
        back=None,
        media_type="text",
        created_at=None,
        updated_at=None,
        deck=None,
        user=None,
    ):
        """
        Inicializa um CardModel representando uma carta de estudo.

        :param _id: ID do documento no MongoDB (gerado automaticamente se não fornecido)
        :param front: Conteúdo da frente da carta
        :param back: Conteúdo do verso da carta
        :param media_type: Tipo de mídia (text, image, audio)
        :param created_at: Data de criação (atualizado automaticamente se não fornecido)
        :param updated_at: Data de atualização (atualizado automaticamente se não fornecido)
        """
        self.id = str(_id) if _id else None
        self.front = front
        self.back = back
        self.media_type = media_type
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.deck = deck
        self.user = user

    def save_to_db(self):
        """Salva ou atualiza a carta no banco de dados MongoDB."""
        card_data = {
            "front": self.front,
            "back": self.back,
            "media_type": self.media_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        if self.id:
            mongo.db.cards.update_one({"_id": ObjectId(self.id)}, {"$set": card_data})
        else:
            result = mongo.db.cards.insert_one(card_data)
            self.id = str(result.inserted_id)
            if self.deck:
                DeckModel.add_cards_to_deck(self.deck, [str(result.inserted_id)])
                UserProgressModel.create_or_update(self.user, self.deck, self.id)

    def delete_from_db(self):
        """Remove a carta do banco de dados MongoDB."""
        if self.id:
            mongo.db.cards.delete_one({"_id": ObjectId(self.id)})

    @staticmethod
    def get_by_id(card_id):
        """Busca um card pelo ID e retorna como dicionário"""
        card = mongo.db.cards.find_one({"_id": ObjectId(card_id)})
        if card:
            result = CardModel(**card)
            return result.to_dict()
        return None

    @staticmethod
    def get_all_cards():
        """Retorna uma lista de todas as cartas no banco de dados."""
        cards = mongo.db.cards.find()
        return [CardModel.from_dict(card) for card in cards]

    @staticmethod
    def from_dict(card_data):
        """Converte um dicionário do MongoDB para uma instância de CardModel."""
        return CardModel(
            _id=card_data.get("_id"),
            front=card_data.get("front"),
            back=card_data.get("back"),
            media_type=card_data.get("media_type", "text"),
            created_at=card_data.get("created_at"),
            updated_at=card_data.get("updated_at"),
        )

    def to_dict(self):
        """Converte a instância de CardModel para um dicionário."""
        return {
            "_id": self.id,
            "front": self.front,
            "back": self.back,
            "media_type": self.media_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
