import random
from bson import ObjectId
from datetime import datetime, timedelta, timezone
from src.app import mongo
from .user_model import UserModel
from .user_progress_model import UserProgressModel
from .deck_model import DeckModel


class ClassroomModel:
    def __init__(self, _id=None, teacher=None,  created_at=None, updated_at=None, students=None, guests=None, name=None, collection=None, collection_data=None, students_data=None, **kwargs):
        self._id = str(_id) if _id else None
        self.name = name
        self.teacher = teacher
        self.students = students or []
        self.guests = guests or []
        self.collection = collection
        self.collection_data = collection_data
        self.students_data = students_data
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        
    def save_to_db(self):
        class_data = {
            'name': self.name,
            'teacher': ObjectId(self.teacher),
            'collection': ObjectId(self.collection),
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'students': self.students
        }
        
        result = mongo.db.classrooms.insert_one(class_data)
        self.id = str(result.inserted_id)

        return {"class_id": str(result.inserted_id)}
    
    @staticmethod
    def get_classrooms_by_user(user_id):
        
        
        pipeline = [
            {"$match": {"teacher": ObjectId(user_id)}},
            {
                "$lookup": {
                    "from": "collections",
                    "localField": "collection",
                    "foreignField": "_id", 
                    "as": "collection_data"
                }
            },
            {
                "$unwind": {
                    "path": "$collection_data",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
            "$lookup": {
                "from": "users",
                "localField": "students",
                "foreignField": "_id",
                "as": "students_data"
            }
        }
        ]

        classrooms = list(mongo.db.classrooms.aggregate(pipeline))
        classrooms_list = [ClassroomModel(**classroom).to_dict() for classroom in classrooms]

        return classrooms_list
    
    
    @staticmethod
    def get_by_id(classroom_id):
        
        pipeline = [
            {"$match": {"_id": ObjectId(classroom_id)}},
            {
                "$lookup": {
                    "from": "collections",
                    "localField": "collection",
                    "foreignField": "_id", 
                    "as": "collection_data"
                }
            },
            {
                "$unwind": {
                    "path": "$collection_data",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
            "$lookup": {
                "from": "users",
                "localField": "students",
                "foreignField": "_id",
                "as": "students_data"
            }
            }
        ]

        classroom = mongo.db.classrooms.aggregate(pipeline)
        classroom = next(classroom, None) 

        if classroom:
            classroom = ClassroomModel(**classroom).to_dict()
            
        return classroom
    
    @staticmethod
    def add_students(classroom_id, user_id):
        
        classroom = ClassroomModel.get_by_id(classroom_id)
        
        mongo.db.classrooms.update_one(
            {"_id": ObjectId(classroom_id)},
            {"$addToSet": {"students": {"$each": [ObjectId(user_id)]}}}
        )
        
        UserModel.add_collections_to_user(user_id, [classroom.get('collection')])
        
        
        for item in classroom.get('decks'):
            deck = DeckModel.get_by_id(item)
            for card_id in deck.get("cards", []):
                UserProgressModel.create_or_update(user_id, deck.get('_id'), card_id)
        
        
    @staticmethod
    def add_guest(classroom_id, email):
        
        mongo.db.classrooms.update_one(
            {"_id": ObjectId(classroom_id)},
            {"$addToSet": {"guests": {"$each": [email]}}}
        )
        
    def to_dict(self):
        """Converte um documento classroom para dicionário"""
        return {
            '_id': self._id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'teacher': str(self.teacher),
            'students': [{'name': student['name'], 'email': student['email']} for student in self.students_data],
            'guests': [guest for guest in self.guests],
            'collection': str(self.collection),
            'image':self.collection_data.get('image'),
            'decks': [str(item) for item in self.collection_data.get('decks')]
        }