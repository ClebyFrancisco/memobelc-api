from flask import Blueprint, jsonify


from ..middlewares.token_required import token_required
from ..models.user_model import find_user_by_email

protected = Blueprint('protected', __name__)

@protected.route('/dashboard', methods=['GET'])
@token_required
def dashboard(current_user):
    user = find_user_by_email(current_user['email'])
    return jsonify({
        'message': f'Welcome {user['name']}! You are authenticated.',
    })
