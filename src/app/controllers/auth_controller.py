from flask import Blueprint, jsonify, request
from ..services.auth_service import create_user, authenticate_user


auth_controller = Blueprint('auth_controller', __name__)


@auth_controller.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if 'email' not in data or 'password' not in data or 'name' not in data:
        return jsonify({'error': 'pending required information'}), 400

    user = create_user(data['name'], data['email'], data['password'])
    if user:
        return jsonify({'message': 'User created successfully'}), 201
    else:
        return jsonify({'error': 'User already exists'}), 400


@auth_controller.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password are required'}), 400

    token = authenticate_user(data['email'], data['password'])
    if token:
        return jsonify({'token': token}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401
