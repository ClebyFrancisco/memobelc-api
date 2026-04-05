from src.app.models.memo_model import MemoModel


class MemoService:

    @staticmethod
    def create_memo(user_id: str, name: str) -> dict:
        memo = MemoModel(user_id=user_id, name=name or "Novo Memo")
        memo_id = memo.save_to_db()
        return {"memo_id": memo_id, "name": memo.name}

    @staticmethod
    def list_memos(user_id: str) -> list[dict]:
        return MemoModel.get_by_user_id(user_id)

    @staticmethod
    def get_memo(memo_id: str, user_id: str) -> dict | None:
        return MemoModel.get_by_id(memo_id, user_id)

    @staticmethod
    def rename_memo(memo_id: str, user_id: str, name: str) -> bool:
        return MemoModel.update_name(memo_id, user_id, name)

    @staticmethod
    def delete_memo(memo_id: str, user_id: str) -> bool:
        return MemoModel.delete(memo_id, user_id)

    @staticmethod
    def save_messages(memo_id: str, user_id: str, messages: list[dict]) -> bool:
        """
        Persists one or more chat messages to the memo history.
        Each message: {"role": "user"|"assistant", "content": str}
        """
        return MemoModel.add_messages(memo_id, user_id, messages)

    @staticmethod
    def clear_messages(memo_id: str, user_id: str) -> bool:
        return MemoModel.clear_messages(memo_id, user_id)
