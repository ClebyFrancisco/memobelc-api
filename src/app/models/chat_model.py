from datetime import datetime, timezone
from bson import ObjectId
from src.app import mongo

class ChatModel:
    """Class to handle chat model"""

    def __init__(self, _id=None, user_id="", settings={}, history =[], created_at=None, updated_at=None,):
        self._id = str(_id) if _id else None
        self.user_id = ObjectId(user_id)
        self.settings = settings
        self.history = history or []
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        

    def save_to_db(self):
        chat = {
            "user_id": self.user_id,
            "settings": self.settings,
            "history": self.history,
            "created_at": self.created_at
        }
        return str(mongo.db.chats.insert_one(chat).inserted_id)

    @staticmethod
    def get_by_user_id(user_id):
        chats = list(mongo.db.chats.find({"user_id": ObjectId(user_id)}))
        for chat in chats:
            chat["_id"] = str(chat["_id"])
            chat["user_id"] = str(chat["user_id"])
        return chats
    
    @staticmethod
    def get_by_id(chat_id):
        chat = mongo.db.chats.find_one({'_id': ObjectId(chat_id)})
        if chat:
            result = ChatModel(**chat)
            return result.to_dict()
        return None

    @staticmethod
    def add_message(chat_id, role, message):
        if not message or not role:
            return {"error": "Invalid data"}, 400
        mongo.db.chats.update_one(
            {"_id": ObjectId(chat_id)},
            {"$push": {"history": {"role": role, "parts": [{"text": message}]}}}
        )
        return {"message": "Added successfully"}

    @staticmethod
    def edit_chat(chat_id, data):
        mongo.db.chats.update_one({"_id": ObjectId(chat_id)}, {"$set": data})
        return {"message": "Chat updated successfully"}

    @staticmethod
    def delete_chat(chat_id):
        mongo.db.chats.delete_one({"_id": ObjectId(chat_id)})
        return {"message": "Chat deleted successfully"}
    
    def to_dict(self):

        return {
        "_id": self._id,
        "user_id": str(self.user_id),
        "settings": self.settings,
        "history": self.history,
        "created_at": self.created_at,
        "updated_at": self.updated_at
        }
