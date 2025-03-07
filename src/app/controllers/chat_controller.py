"""Module for handling chat-related endpoints."""

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest, Unauthorized
from src.app.middlewares.token_required import token_required
from src.app.services.chat_service import ChatService

class ChatController:
    @staticmethod
    @token_required
    def chat(current_user, token):

        data = request.get_json()
        
        history = data.get("history", [])
        id = data.get('id', None)
        message =data.get('message', '')
        settings = data.get("settings", {})
        
        return ChatService.chat(current_user._id, id,  history, settings, message)
       


chat_blueprint = Blueprint("chat_blueprint", __name__)
chat_blueprint.route("/", methods=["POST"])(ChatController.chat)