"""Module for handling chat-related endpoints."""

import json
import jwt
from flask import Blueprint, request, jsonify, current_app
from src.app.middlewares.token_required import token_required
from src.app.services.chat_service import ChatService
from src.app.models.user_model import UserModel
from src.app.extensions import sock

class ChatController:
    @staticmethod
    @token_required
    def chat(current_user, token):
        data = request.get_json() or {}
        history = data.get("history", [])
        id = data.get("id", None)
        message = data.get("message", "")
        settings = data.get("settings", {})
        try:
            result = ChatService.chat(
                current_user._id, id, history, settings, message
            )
            return jsonify(result), 200
        except Exception as e:
            if "429" in str(type(e).__name__) or "ResourceExhausted" in str(e):
                return jsonify({"error": "API quota exceeded"}), 429
            return jsonify({"error": str(e)}), 500
    
    @staticmethod
    @token_required
    def get_chats_by_user_id(current_user, token):
        response = ChatService.get_chats_by_user_id(current_user._id)
        return jsonify(response), 200
    
    def generate_cards_by_chat():
        data = request.get_json() or {}
        response = ChatService.generate_card(
            chat_id=data.get("chat_id"), settings=data.get("settings")
        )
        if response is None:
            return jsonify({"error": "Chat not found"}), 404
        return jsonify(response), 200
    

chat_blueprint = Blueprint("chat_blueprint", __name__)
chat_blueprint.route("/talk_to_me", methods=["POST"])(ChatController.chat)
chat_blueprint.route("/get_chats_by_user", methods=["GET"])(ChatController.get_chats_by_user_id)
chat_blueprint.route('/generate_card', methods=["POST"])(ChatController.generate_cards_by_chat)


def _get_user_from_token(token):
    payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    current_user = UserModel.find_by_email(payload["email"])
    if not current_user:
        raise ValueError("User not found")
    return current_user


@sock.route("/chat/realtime")
def chat_realtime(ws):
    current_user = None
    session_state = {
        "chat_id": None,
        "settings": {"language_conversation": "en-US"},
        "history": [],
        "audio_chunks": [],
        "audio_mime": "audio/webm",
    }

    try:
        while True:
            data = ws.receive()
            if data is None:
                break

            payload = json.loads(data)
            event = payload.get("event")
            body = payload.get("data", {})

            if event == "session.start":
                token = body.get("token")
                if not token:
                    ws.send(json.dumps({"event": "error", "data": {"message": "Missing token"}}))
                    continue
                current_user = _get_user_from_token(token)
                session_state["chat_id"] = body.get("chat_id")
                session_state["settings"] = body.get("settings", {"language_conversation": "en-US"})
                session_state["history"] = body.get("history", [])
                session_state["audio_chunks"] = []
                session_state["audio_mime"] = body.get("mime_type", "audio/webm")
                ws.send(json.dumps({"event": "session.started", "data": {"chat_id": session_state["chat_id"]}}))

            elif event == "audio.input.chunk":
                chunk = body.get("chunk")
                if chunk:
                    session_state["audio_chunks"].append(chunk)
                if body.get("mime_type"):
                    session_state["audio_mime"] = body.get("mime_type")

            elif event == "audio.input.commit":
                if not current_user:
                    ws.send(json.dumps({"event": "error", "data": {"message": "Session not started"}}))
                    continue
                if not session_state["audio_chunks"]:
                    ws.send(json.dumps({"event": "error", "data": {"message": "No audio chunk received"}}))
                    continue

                ws.send(json.dumps({"event": "transcript.partial", "data": {"text": "Processing audio..."}}))
                audio_base64 = "".join(session_state["audio_chunks"])
                turn_result = ChatService.process_voice_turn(
                    user_id=current_user._id,
                    chat_id=session_state["chat_id"],
                    history=session_state["history"],
                    settings=session_state["settings"],
                    audio_base64=audio_base64,
                    audio_mime=body.get("mime_type") or session_state["audio_mime"],
                )
                session_state["chat_id"] = turn_result["chat_id"]
                session_state["history"].append({"role": "user", "parts": [{"text": turn_result["transcript"]}]})
                session_state["history"].append({"role": "model", "parts": [{"text": turn_result["reply"]}]})
                session_state["audio_chunks"] = []

                ws.send(json.dumps({"event": "transcript.final", "data": {"text": turn_result["transcript"]}}))
                ws.send(
                    json.dumps(
                        {
                            "event": "assistant.text",
                            "data": {"text": turn_result["reply"], "chat_id": turn_result["chat_id"]},
                        }
                    )
                )
                ws.send(
                    json.dumps(
                        {
                            "event": "assistant.audio.chunk",
                            "data": {
                                "chunk": turn_result["audio_base64"],
                                "mime_type": turn_result["audio_mime"],
                            },
                        }
                    )
                )
                ws.send(json.dumps({"event": "assistant.audio.end", "data": {"chat_id": turn_result["chat_id"]}}))

            elif event in ("session.interrupt", "session.end"):
                session_state["audio_chunks"] = []
                ws.send(json.dumps({"event": "session.ended", "data": {"chat_id": session_state["chat_id"]}}))
                if event == "session.end":
                    break
            else:
                ws.send(json.dumps({"event": "error", "data": {"message": f"Unknown event: {event}"}}))
    except Exception as e:
        ws.send(
            json.dumps(
                {
                    "event": "error",
                    "data": {
                        "message": str(e),
                        "type": type(e).__name__,
                    },
                }
            )
        )
