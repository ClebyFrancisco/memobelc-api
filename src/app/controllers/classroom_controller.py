
from flask import Blueprint, jsonify, request, Response, current_app
from werkzeug.exceptions import BadRequest, Unauthorized
from src.app.services.collections_service import CollectionService
from src.app.services.classroom_service import ClassroomService
from src.app.services.chat_service import ChatService
from src.app.middlewares.token_required import token_required

class ClassroomController:
    
    @staticmethod
    @token_required
    def createClassroom(current_user, token):
        data = request.get_json()
        if ("collection_id") not in data:
            return BadRequest(description="the fields are mandatory")
        
        if current_user.role != "teacher":
            return Unauthorized(description="User Invalid!")
        
        result = ClassroomService.createClassroom(collection_id=data.get('collection_id'), user_id=current_user._id )
        return jsonify(result), 200
    
    @staticmethod
    @token_required
    def getClassrooms(current_user, token):
        
        result = ClassroomService.getClassrooms(user_id=current_user._id)
        return jsonify(result), 200
    
    
    @staticmethod
    @token_required
    def add_students(current_user, token):
        data = request.get_json()
        if current_user.role != "teacher":
            return Unauthorized(description="User Invalid!")
        
        if "classroom_id" not in data or "email_user" not in data:
            return BadRequest(description="The fields 'classroom_id' and 'email_user' are mandatory")
        
        result = ClassroomService.add_students(classroom_id=data.get('classroom_id'), email_user=data.get('email_user'))
        return jsonify(result), 200
    
    
    def generate_cards_by_subject():
        data = request.get_json()
        
        if "subject" not in data:
            return jsonify({"error": "Subject is required!"}), 400
        
        if "amount" in data:
            amount = data["amount"]
        else:
            amount = 20

        if "language_front" not in data or "language_back" not in data:
            return jsonify({"error":"language of cards front and back is required"}), 400
            
        if "deck_id" in data:
            deck_id = data["deck_id"]
        else:
            deck_id = None
            
        if "deck_name" in data:
            deck_name = data["deck_name"]
        else:
            deck_name = None
            
        if "format" in data:
            format = data["format"]
        else:
            format = None
            
        try:
            response = ChatService.generate_cards_by_subject(
                subject=data.get("subject"),
                amount=amount,
                deck_id=deck_id,
                deck_name=deck_name,
                language_front=data.get("language_front"),
                language_back=data.get("language_back"),
                format=format,
            )
            return jsonify(response), 200
        except Exception as e:
            if "429" in str(type(e).__name__) or "ResourceExhausted" in str(e):
                return jsonify({"error": "API quota exceeded"}), 429
            return jsonify({"error": str(e)}), 500

        
        
        
classroom_blueprint = Blueprint("classroom_blueprint", __name__)
classroom_blueprint.route("/create", methods=["POST"])(ClassroomController.createClassroom)
classroom_blueprint.route("/get_classrooms", methods=['GET'])(ClassroomController.getClassrooms)
classroom_blueprint.route("/add_user_in_classroom", methods=['POST'])(ClassroomController.add_students)
classroom_blueprint.route("/generate_cards_by_subject", methods=["POST"])(ClassroomController.generate_cards_by_subject)

        