from datetime import datetime, timedelta
from bson import ObjectId
from src.app import mongo

class UserProgressModel:
    def __init__(self, user_id, deck_id, card_id, status="pendente", attempts=0, last_reviewed=None, next_review=None):
        self.user_id = ObjectId(user_id)
        self.deck_id = ObjectId(deck_id)
        self.card_id = ObjectId(card_id)
        self.status = status
        self.attempts = attempts
        self.last_reviewed = last_reviewed or datetime.utcnow()
        self.next_review = next_review or self.calculate_next_review()

    def calculate_next_review(self):
        """Define a próxima revisão com base no número de tentativas (espaçamento progressivo)."""
        # Espaçamento básico: 1, 3, 7 dias (ou qualquer outro algoritmo desejado)
        if self.attempts == 0:
            return datetime.utcnow()
        elif self.attempts == 1:
            # return datetime.utcnow() + timedelta(days=1)
            return datetime.utcnow() + timedelta(minutes=5)
        elif self.attempts == 2:
            return datetime.utcnow() + timedelta(days=3)
        elif self.attempts == 3:
            return datetime.utcnow() + timedelta(days=7)
        else :
            return datetime.utcnow() + timedelta(days=self.attempts*7)

    def save_to_db(self):
        """Salva o progresso do usuário no banco de dados MongoDB."""
        progress_data = {
            "user_id": self.user_id,
            "deck_id": self.deck_id,
            "card_id": self.card_id,
            "status": self.status,
            "attempts": self.attempts,
            "last_reviewed": None,
            "next_review": datetime.utcnow()
        }
        mongo.db.user_progress.insert_one(progress_data)

    def update_status(self, new_status):
        """Atualiza o status da carta e recalcula a data de próxima revisão."""
        self.status = new_status
        self.attempts += 1
        self.last_reviewed = datetime.utcnow()
        self.next_review = self.calculate_next_review()
        mongo.db.user_progress.update_one(
            {"user_id": self.user_id, "deck_id": self.deck_id, "card_id": self.card_id},
            {"$set": {
                "status": self.status,
                "attempts": self.attempts,
                "last_reviewed": self.last_reviewed,
                "next_review": self.next_review
            }}
        )

    @staticmethod
    def get_pending_cards(user_id, deck_id=None):
        """Recupera cartas pendentes de revisão no dia atual."""
        query = {
            "user_id": ObjectId(user_id),
            "next_review": {"$lte": datetime.utcnow()},
        }
        if deck_id:
            query["deck_id"] = ObjectId(deck_id)

        pending_cards = mongo.db.user_progress.find(query)
        return [
            {
                "user_id": str(card["user_id"]),
                "deck_id": str(card["deck_id"]),
                "card_id": str(card["card_id"]),
                "status": card["status"],
                "attempts": card["attempts"],
                "last_reviewed": card["last_reviewed"],
                "next_review": card["next_review"]
            }
            for card in pending_cards
        ]

    @staticmethod
    def create_or_update(user_id, deck_id, card_id, new_status="pendente"):
        """Cria ou atualiza o progresso de um usuário em uma carta específica."""
        existing_record = mongo.db.user_progress.find_one({
            "user_id": ObjectId(user_id),
            "deck_id": ObjectId(deck_id),
            "card_id": ObjectId(card_id)
        })

        if existing_record:
            # Atualiza o status se já existe um registro
            user_progress = UserProgressModel(
                user_id=existing_record["user_id"],
                deck_id=existing_record["deck_id"],
                card_id=existing_record["card_id"],
                status=existing_record["status"],
                attempts=existing_record["attempts"],
                last_reviewed=existing_record["last_reviewed"],
                next_review=existing_record["next_review"]
            )
            user_progress.update_status(new_status)
        else:
            # Cria um novo progresso se não existe
            new_progress = UserProgressModel(user_id, deck_id, card_id, status=new_status)
            new_progress.save_to_db()

