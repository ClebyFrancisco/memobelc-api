from flask import Blueprint, jsonify
from ..middlewares.token_required import token_required
from ..models.user_model import UserModel

class ProtectedController:
    def __init__(self):
        self.protected_bp = Blueprint('protected', __name__)
        self.register_routes()

    def register_routes(self):
        @self.protected_bp.route('/dashboard', methods=['GET'])
        @token_required
        def dashboard(current_user):
            # Aqui o current_user é um objeto de UserModel
            user = UserModel.find_by_email(current_user.email)
            
            if user:
                return jsonify({
                    'message': f'Welcome {user.name}! You are authenticated.',
                })
            else:
                return jsonify({'error': 'User not found'}), 404

# Crie uma instância do controlador e adicione o Blueprint ao aplicativo
protected_controller = ProtectedController()
protected_bp = protected_controller.protected_bp

