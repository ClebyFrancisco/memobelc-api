"""Module for handling chat-related endpoints."""

from flask import Blueprint, request
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
    
    
    def generate_card():
        pass
        


chat_blueprint = Blueprint("chat_blueprint", __name__)
chat_blueprint.route("/talk_to_me", methods=["POST"])(ChatController.chat)
chat_blueprint.route('/get_chats', methods=["GET"])(ChatController.generate_card)