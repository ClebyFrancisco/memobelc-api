from flask import Blueprint, jsonify, request
from src.app.services.invite_service import InviteService
from src.app.middlewares.token_required import token_required


class InviteController:
    """Controller para gerenciar convites de usuários"""

    @staticmethod
    @token_required
    def send_invite_by_email(current_user, token):
        """Envia um convite por email"""
        data = request.get_json()
        if not data or "email" not in data:
            return jsonify({"error": "Email é obrigatório"}), 400
        
        email = data["email"].lower().strip()
        return InviteService.send_invite_by_email(str(current_user._id), email)

    @staticmethod
    @token_required
    def generate_invite_link(current_user, token):
        """Gera um link de convite único"""
        return InviteService.generate_invite_link(str(current_user._id))

    @staticmethod
    @token_required
    def get_user_invites(current_user, token):
        """Retorna todos os convites feitos pelo usuário"""
        return InviteService.get_user_invites(str(current_user._id))

    @staticmethod
    @token_required
    def get_user_invited_friends(current_user, token):
        """Retorna a lista de amigos convidados do usuário"""
        return InviteService.get_user_invited_friends(str(current_user._id))

    @staticmethod
    def verify_invite_code():
        """Verifica se um código de convite é válido (público)"""
        data = request.get_json()
        if not data or "invite_code" not in data:
            return jsonify({"error": "Código de convite é obrigatório"}), 400
        
        return InviteService.verify_invite_code(data["invite_code"])


invite_blueprint = Blueprint("invite_blueprint", __name__)

invite_blueprint.route("/invite/email", methods=["POST"])(InviteController.send_invite_by_email)
invite_blueprint.route("/invite/link", methods=["POST"])(InviteController.generate_invite_link)
invite_blueprint.route("/invite/list", methods=["GET"])(InviteController.get_user_invites)
invite_blueprint.route("/invite/friends", methods=["GET"])(InviteController.get_user_invited_friends)
invite_blueprint.route("/invite/verify", methods=["POST"])(InviteController.verify_invite_code)

