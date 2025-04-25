from src.app.models.classroom_model import ClassroomModel
from src.app.models.collection_model import CollectionModel
from src.app.models.user_model import UserModel

class ClassroomService:
    
    @staticmethod
    def createClassroom(collection_id, user_id):
        collection = CollectionModel.get_by_id(collection_id)
        classrooms = ClassroomModel(name=collection.get('name'), teacher=user_id, collection=collection_id)
        result = classrooms.save_to_db()
        
        CollectionModel.add_classroom(result.get('class_id'), classrooms.collection)
        return result
    
    @staticmethod
    def getClassrooms(user_id):
        result = ClassroomModel.get_classrooms_by_user(user_id)
        return {'classrooms':result}
    
    @staticmethod
    def add_students(classroom_id, email_user):
        user = UserModel.find_by_email(email_user)
        
        if user:
            ClassroomModel.add_students(classroom_id, user._id)
            
        else:
            ClassroomModel.add_guest(classroom_id, email_user)
        
        return {}

        
