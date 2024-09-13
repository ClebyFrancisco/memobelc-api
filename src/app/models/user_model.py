from src.app import mongo

def find_user_by_email(email):
    return mongo.db.users.find_one({'email': email})

# def find_user_by_id(id):
#     return mongo.db.user.find_one({'id': id })
    

def create_user_in_db(name, email, hashed_password):
    user = {
        'name': name,
        'email': email, 
        'password': hashed_password
    }
    return mongo.db.users.insert_one(user)
