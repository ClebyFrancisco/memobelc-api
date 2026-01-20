"""Model class for user_notification_settings"""

from datetime import datetime, timezone
from bson import ObjectId
from src.app import mongo
from src.app.models.deck_model import DeckModel
from src.app.models.user_progress_model import UserProgressModel


class UserSettingsModel:

    @staticmethod
    def get_settings(user_id):
        return mongo.db.user_notification_settings.find_one({"user_id": user_id}) or {}

    @staticmethod
    def update_settings(user_id, settings):
        mongo.db.user_notification_settings.update_one(
            {"user_id": user_id},
            {"$set": settings},
            upsert=True
        )
