from flask import Blueprint, jsonify
from ..middlewares.token_required import token_required

protected = Blueprint('protected', __name__)

@protected.route('/dashboard', methods=['GET'])
@token_required
def dashboard(current_user):
    print(current_user)
    return jsonify({
        'message': f'Welcome {current_user["name"]}! You are authenticated.',
        'email': current_user['email']
    })
