"""Model class for videos"""

from datetime import datetime, timezone
from bson import ObjectId
from src.app import mongo

class VideoModel:

    def __init__(self, _id=None, title=None, created_at=None, updated_at=None, thumbnail=None, deck_id=None, video_id=None):
        self._id = str(_id) if _id else None
        self.title = title
        self.thumbnail = thumbnail
        self.video_id = video_id
        self.deck_id = ObjectId(deck_id)
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        
    def save_to_db(self):
        """Salva ou atualiza um video no banco de dados MongoDB."""
        video_data = {
            "title": self.title,
            "thumbnail": self.thumbnail,
            "video_id": self.video_id,
            "deck_id": self.deck_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        if self._id:
            mongo.db.videos.update_one({"_id": ObjectId(self._id)}, {"$set": video_data})
        else:
            result = mongo.db.videos.insert_one(video_data)
            self._id = str(result.inserted_id)
            return str(result.inserted_id)
        
        
    @staticmethod
    def get_all_videos():
        """Retorna todos os videos como uma lista de dicionários"""
        videos = mongo.db.videos.find()
        return [VideoModel(**video).to_dict() for video in videos]

        
    def to_dict(self):
        """Converte a instância de VideoModel para um dicionário."""
        return {
            "_id": self._id,
            "title": self.title,
            "thumbnail": self.thumbnail,
            "video_id": self.video_id,
            "deck_id": str(ObjectId(self.deck_id)),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
