from datetime import datetime, timedelta, timezone
from bson import ObjectId
from src.app import mongo

class UserProgressModel:
    def __init__(self, _id=None, user_id=None, deck_id=None, card_id=None, attempts=0, last_reviewed=None, next_review=None):
        self._id = str(_id) if _id else None
        self.user_id = ObjectId(user_id)
        self.deck_id = ObjectId(deck_id)
        self.card_id = ObjectId(card_id)
        self.attempts = attempts
        self.last_reviewed = last_reviewed or datetime.now(timezone.utc)
        self.next_review = next_review or self.calculate_next_review()

    def calculate_next_review(self, recall_level=None):
        """Define a próxima revisão com base no recall_level e no número de tentativas."""
        
        if recall_level:
        
            spacing = {
                "i_dont_remember": "",  
                "difficult": timedelta(days=1), 
                "good": lambda attempts: timedelta(days=1 * (2 ** (attempts - 1))),
                "easy": lambda attempts: timedelta(days=2 * (2 ** (attempts - 1))) 
            }
            if recall_level in ["i_dont_remember"]:
                return datetime.now(timezone.utc)
            
            if recall_level in ["difficult"]:
                return datetime.now(timezone.utc) + spacing[recall_level]
            
            return datetime.now(timezone.utc) + spacing[recall_level](self.attempts)
        
        else :
            return datetime.now(timezone.utc)


    def save_to_db(self):
        """Salva o progresso do usuário no banco de dados MongoDB."""
        progress_data = {
            "user_id": self.user_id,
            "deck_id": self.deck_id,
            "card_id": self.card_id,
            "attempts": self.attempts,
            "last_reviewed": None,
            "next_review": datetime.now(timezone.utc)
        }
        mongo.db.user_progress.insert_one(progress_data)

    @staticmethod
    def update_status(user_id, card_id, recall_level):
        """Atualiza o status da carta e recalcula a data de próxima revisão."""
        
        query = {
            "user_id": ObjectId(user_id),
            "card_id": ObjectId(card_id)
        }
        
        card_progress = mongo.db.user_progress.find_one(query)
        progress = UserProgressModel(**card_progress)
        
        attempts = progress.attempts + 1
        last_reviewed = progress.last_reviewed = datetime.now(timezone.utc)
        next_review = progress.calculate_next_review(recall_level)
        mongo.db.user_progress.update_one(
            {"user_id": progress.user_id, "deck_id": progress.deck_id, "card_id": progress.card_id},
            {"$set": {
                "attempts": attempts,
                "last_reviewed": last_reviewed,
                "next_review": next_review
            }}
        )
        
        return "ok"

    @staticmethod
    def get_pending_cards(user_id, deck_id=None):
        """Recupera cartas pendentes de revisão no dia atual, incluindo front e back."""
        
        query = {
            "user_id": ObjectId(user_id),
            "next_review": {"$lte": datetime.now(timezone.utc)},
        }
        if deck_id:
            query["deck_id"] = ObjectId(deck_id)

        pipeline = [
            {"$match": query},
            {
                "$lookup": {
                    "from": "cards",
                    "localField": "card_id",
                    "foreignField": "_id",
                    "as": "card_details"
                }
            },
            {"$unwind": "$card_details"}
        ]

        pending_cards = mongo.db.user_progress.aggregate(pipeline)
        
        return [
            {
                "card_id": str(card["card_id"]),
                "last_reviewed": card["last_reviewed"],
                "next_review": card["next_review"],
                "front": card["card_details"]["front"],
                "back": card["card_details"]["back"],
                "audio": card["card_details"].get("audio",  None),
            }
            for card in pending_cards
        ]

    @staticmethod
    def create_or_update(user_id, deck_id, card_id):
        """Cria ou atualiza o progresso de um usuário em uma carta específica."""
        existing_record = mongo.db.user_progress.find_one({
            "user_id": ObjectId(user_id),
            "deck_id": ObjectId(deck_id),
            "card_id": ObjectId(card_id)
        })

        if existing_record:
            return
        else:
            
            new_progress = UserProgressModel(user_id=user_id, deck_id=deck_id, card_id=card_id)
            new_progress.save_to_db()

    @staticmethod
    def count_pending_cards(user_id, deck_id=None):
        
        query = {
            "user_id": ObjectId(user_id),
            "next_review": {"$lte": datetime.now(timezone.utc)},
        }
       
        if deck_id:
            query["deck_id"] = ObjectId(deck_id)

        
        pending_cards = mongo.db.user_progress.count_documents(query)
        return pending_cards