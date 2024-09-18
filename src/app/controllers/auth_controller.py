from flask import Blueprint, jsonify, request, Response, current_app
from ..services.auth_service import AuthService


class AuthController:
    def __init__(self):
        self.auth_service = AuthService()

    def register(self):
        data = request.get_json()

        # Verificação de campos obrigatórios
        if 'email' not in data or 'password' not in data or 'name' not in data:
            return jsonify({'error': 'Missing required information'}), 400

        # Chama o serviço para criar o usuário
        user = self.auth_service.create_user(data['name'], data['email'], data['password'])
        if user:
            return jsonify({'message': 'User created successfully'}), 201
        else:
            return jsonify({'error': 'User already exists'}), 400

    def login(self):
        data = request.get_json()

        # Verificação de campos obrigatórios
        if 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400

        # Chama o serviço para autenticar o usuário
        token = self.auth_service.authenticate_user(data['email'], data['password'])
        if token:
            if current_app.config['FLASK_ENV'] == 'development':
                return jsonify({'Token': token}), 200
            else:
                serialized_response = bytes(token)
                return Response(serialized_response, mimetype='application/octet-stream', status=200)

        else:
            return jsonify({'error': 'Invalid credentials'}), 401


# Instância da classe AuthController
auth_controller = AuthController()

# Blueprint para as rotas de autenticação
auth_blueprint = Blueprint('auth_blueprint', __name__)

# Definindo as rotas
auth_blueprint.route('/register', methods=['POST'])(auth_controller.register)
auth_blueprint.route('/login', methods=['POST'])(auth_controller.login)