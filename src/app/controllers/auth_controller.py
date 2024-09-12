from flask import Blueprint, jsonify, request


auth_controller = Blueprint('auth_controller', __name__)


@auth_controller.route('/login', methods=['GET'])
def login():
    return 'Hello, World!'