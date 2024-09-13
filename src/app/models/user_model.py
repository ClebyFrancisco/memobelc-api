from src.app import mongo
import uuid

def find_user_by_email(email):
    return mongo.db.users.find_one({'email': email})

def find_user_by_id(id):
    return mongo.db.user.find_one({'user_id': id })
    

def create_user_in_db(name, email, hashed_password):
    unique_id = f'{uuid.uuid4()}'
    user = {
        'user_id': unique_id,
        'name': name,
        'email': email, 
        'password': hashed_password
    }
    return mongo.db.users.insert_one(user)
