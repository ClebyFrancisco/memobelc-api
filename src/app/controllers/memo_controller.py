"""Endpoints for Memo management (document-grounded RAG chats)."""

from flask import Blueprint, request, jsonify
from src.app.middlewares.token_required import token_required
from src.app.services.memo_service import MemoService


class MemoController:

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @staticmethod
    @token_required
    def create(current_user, token):
        data = request.get_json() or {}
        name = data["name"]
        result = MemoService.create_memo(str(current_user._id), name)
        return jsonify(result), 201

    @staticmethod
    @token_required
    def list_memos(current_user, token):
        memos = MemoService.list_memos(str(current_user._id))
        return jsonify({"memos": memos}), 200

    @staticmethod
    @token_required
    def get_memo(current_user, token, memo_id):
        memo = MemoService.get_memo(memo_id, str(current_user._id))
        if not memo:
            return jsonify({"error": "Memo não encontrado"}), 404
        return jsonify(memo), 200

    @staticmethod
    @token_required
    def rename(current_user, token, memo_id):
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"error": "Nome inválido"}), 400
        updated = MemoService.rename_memo(memo_id, str(current_user._id), name)
        if not updated:
            return jsonify({"error": "Memo não encontrado"}), 404
        return jsonify({"message": "Memo renomeado com sucesso"}), 200

    @staticmethod
    @token_required
    def delete(current_user, token, memo_id):
        deleted = MemoService.delete_memo(memo_id, str(current_user._id))
        if not deleted:
            return jsonify({"error": "Memo não encontrado"}), 404
        return jsonify({"message": "Memo removido com sucesso"}), 200

    # ------------------------------------------------------------------
    # Messages (chat history)
    # ------------------------------------------------------------------

    @staticmethod
    @token_required
    def save_messages(current_user, token, memo_id):
        """
        Body: { "messages": [{"role": "user"|"assistant", "content": "..."}] }
        Appends messages to the memo's chat history.
        """
        data = request.get_json() or {}
        messages = data.get("messages", [])
        if not messages:
            return jsonify({"error": "Nenhuma mensagem fornecida"}), 400
        saved = MemoService.save_messages(memo_id, str(current_user._id), messages)
        if not saved:
            return jsonify({"error": "Memo não encontrado"}), 404
        return jsonify({"message": "Mensagens salvas com sucesso"}), 200

    @staticmethod
    @token_required
    def clear_messages(current_user, token, memo_id):
        cleared = MemoService.clear_messages(memo_id, str(current_user._id))
        if not cleared:
            return jsonify({"error": "Memo não encontrado"}), 404
        return jsonify({"message": "Histórico limpo com sucesso"}), 200


memo_blueprint = Blueprint("memo_blueprint", __name__)

memo_blueprint.route("/", methods=["POST"])(MemoController.create)
memo_blueprint.route("/", methods=["GET"])(MemoController.list_memos)
memo_blueprint.route("/<memo_id>", methods=["GET"])(MemoController.get_memo)
memo_blueprint.route("/<memo_id>", methods=["PATCH"])(MemoController.rename)
memo_blueprint.route("/<memo_id>", methods=["DELETE"])(MemoController.delete)
memo_blueprint.route("/<memo_id>/messages", methods=["POST"])(MemoController.save_messages)
memo_blueprint.route("/<memo_id>/messages", methods=["DELETE"])(MemoController.clear_messages)
