from src.app import mongo

def find_user_by_email(email):
    return mongo.db.users.find_one({'email': email})

def create_user_in_db(email, hashed_password):
    user = {
        'email': email,
        'password': hashed_password
    }
    return mongo.db.users.insert_one(user)
