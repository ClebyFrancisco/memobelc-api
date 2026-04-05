from datetime import datetime, timezone
from bson import ObjectId
from src.app import mongo


class MemoModel:
    """MongoDB model for user memos (document-grounded RAG chats)."""

    def __init__(self, _id=None, user_id="", name="Novo Memo", messages=None,
                 created_at=None, updated_at=None, **kwargs):
        self._id = str(_id) if _id else None
        self.user_id = ObjectId(user_id)
        self.name = name
        self.messages = messages or []
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def save_to_db(self) -> str:
        doc = {
            "user_id": self.user_id,
            "name": self.name,
            "messages": self.messages,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        return str(mongo.db.memos.insert_one(doc).inserted_id)

    @staticmethod
    def update_name(memo_id: str, user_id: str, name: str) -> bool:
        result = mongo.db.memos.update_one(
            {"_id": ObjectId(memo_id), "user_id": ObjectId(user_id)},
            {"$set": {"name": name, "updated_at": datetime.now(timezone.utc)}},
        )
        return result.modified_count > 0

    @staticmethod
    def add_messages(memo_id: str, user_id: str, messages: list[dict]) -> bool:
        """Appends one or more {role, content, timestamp} messages to history."""
        now = datetime.now(timezone.utc)
        for msg in messages:
            msg.setdefault("timestamp", now)
        result = mongo.db.memos.update_one(
            {"_id": ObjectId(memo_id), "user_id": ObjectId(user_id)},
            {
                "$push": {"messages": {"$each": messages}},
                "$set": {"updated_at": now},
            },
        )
        return result.modified_count > 0

    @staticmethod
    def clear_messages(memo_id: str, user_id: str) -> bool:
        result = mongo.db.memos.update_one(
            {"_id": ObjectId(memo_id), "user_id": ObjectId(user_id)},
            {"$set": {"messages": [], "updated_at": datetime.now(timezone.utc)}},
        )
        return result.modified_count > 0

    @staticmethod
    def delete(memo_id: str, user_id: str) -> bool:
        result = mongo.db.memos.delete_one(
            {"_id": ObjectId(memo_id), "user_id": ObjectId(user_id)}
        )
        return result.deleted_count > 0

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    @staticmethod
    def get_by_user_id(user_id: str) -> list[dict]:
        """Returns all memos for a user without the messages array (for listing)."""
        memos = list(
            mongo.db.memos.find(
                {"user_id": ObjectId(user_id)},
                {"messages": 0},
            ).sort("updated_at", -1)
        )
        for m in memos:
            m["_id"] = str(m["_id"])
            m["user_id"] = str(m["user_id"])
        return memos

    @staticmethod
    def get_by_id(memo_id: str, user_id: str) -> dict | None:
        """Returns a single memo with full message history, only if it belongs to user."""
        memo = mongo.db.memos.find_one(
            {"_id": ObjectId(memo_id), "user_id": ObjectId(user_id)}
        )
        if not memo:
            return None
        memo["_id"] = str(memo["_id"])
        memo["user_id"] = str(memo["user_id"])
        for msg in memo.get("messages", []):
            if "timestamp" in msg and hasattr(msg["timestamp"], "isoformat"):
                msg["timestamp"] = msg["timestamp"].isoformat()
        return memo
