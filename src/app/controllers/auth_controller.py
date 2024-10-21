from flask import Blueprint, jsonify, request, Response, current_app
from ..services.auth_service import AuthService
from ..middlewares.token_required import token_required
from src.app import mail
from ..proto.pb.auth import LoginRequest, RefreshToken
from ..middlewares.token_required import token_required
from ..models.user_model import UserModel



class AuthController:
    @staticmethod
    def register():
        data = request.get_json()

        # Verificação de campos obrigatórios
        if 'email' not in data or 'password' not in data or 'name' not in data:
            return jsonify({'error': 'Missing required information'}), 400

        # Chama o serviço para criar o usuário
        user = AuthService.create_user(data['name'], data['email'], data['password'])
        if user:
            return jsonify({'message': 'User created successfully'}), 201
        else:
            return jsonify({'error': 'User already exists'}), 400


    @staticmethod
    def login():
        if current_app.config['FLASK_ENV'] == 'development':
            
            data = request.get_json()
            
            # Verificação de campos obrigatórios
            if 'email' not in data or 'password' not in data:
                return jsonify({'error': 'Email and password are required'}), 400
            
            # Chama o serviço para autenticar o usuário
            token = AuthService.authenticate_user(data['email'], data['password'])
            if token:
                return jsonify(token), 200
            else:
                return jsonify({'error': 'Invalid credentials'}), 401
        else:
            
            data = request.data
            login_request = LoginRequest().parse(data)

            if not login_request.email or not login_request.password :
                error_response = ErrorResponse(error="Email and password are required")
                return Response(bytes(error_response), status=400, mimetype='application/x-protobuf')
            
            token = AuthService.authenticate_user(login_request.email, login_request.password)
        
            if token:
                serialized_response = bytes(token)
                return Response(serialized_response, mimetype='application/octet-stream', status=200)


    @staticmethod
    def refresh_token():
        if current_app.config['FLASK_ENV'] == 'development':
            
            data = request.get_json()
            
            # Verificação de campos obrigatórios
            if 'token' not in data:
                return jsonify({'error': 'token is required'}), 400
            
            # Chama o serviço para autenticar o usuário
            token = AuthService.refresh_token(data['token'])
            if token:
                return jsonify(token), 200
            else:
                return jsonify({'error': 'Invalid credentials'}), 401
        else:
            
            data = request.data
            refresh_request = RefreshToken().parse(data)

            if not refresh_request.token:
                error_response = ErrorResponse(error="token is missing")
                return Response(bytes(error_response), status=400, mimetype='application/x-protobuf')
            
            token = AuthService.refresh_token(refresh_request.token)
        
            if token:
                serialized_response = bytes(token)
                return Response(serialized_response, mimetype='application/octet-stream', status=200)
    
    @staticmethod
    @token_required    
    def verify_code(current_user, token):
        user = UserModel.find_by_email(current_user.email)

        print(user.email)
        
        data = request.get_json()
        
        response = AuthService.verify_code(current_user, data['code'])
        
        if response :
            # Chama o serviço para autenticar o usuário
            token = AuthService.refresh_token(token)
            return jsonify(token), 200
        else:
            return jsonify("Código inválido"), 401
        


        
# Blueprint para as rotas de autenticação
auth_blueprint = Blueprint('auth_blueprint', __name__)

# Definindo as rotas
auth_blueprint.route('/register', methods=['POST'])(AuthController.register)
auth_blueprint.route('/login', methods=['POST'])(AuthController.login)
auth_blueprint.route('/refresh_token', methods=['POST'])(AuthController.refresh_token)
auth_blueprint.route('/verify_code', methods=['POST'])(AuthController.verify_code)