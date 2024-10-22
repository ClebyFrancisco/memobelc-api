from src.app import mongo
import random
import string

class UserModel:
    def __init__(self, _id=None, name = None, email=None, password=None, **kwargs):
        self._id = str(_id) if _id else None
        self.name = name
        self.email = email
        self.password = password


    def save_to_db(self):
        """Salva o usuário no banco de dados MongoDB"""
        user_data = {
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'is_confirmed': False
        }
        mongo.db.users.insert_one(user_data)
        self.generate_code(user_data['email'])
        return True

    @staticmethod
    def find_by_email(email):
        """Busca um usuário pelo email"""
        user_data = mongo.db.users.find_one({'email': email})
        if user_data:
            return UserModel(**user_data)
        return None

    @staticmethod
    def find_by_id(user_id):
        """Busca um usuário pelo ID"""
        user_data = mongo.db.users.find_one({'_id': user_id})
        if user_data:
            return UserModel(**user_data)
        return None
    
    @staticmethod
    def verify_is_confirmed(email):
        """Verificar se um usuário está confirmado!"""
        user_data = mongo.db.users.find_one({'email': email})
        if user_data and user_data['is_confirmed']:
            return True
        else:
            return False
        
        
    @staticmethod
    def verify_code(email, code):
        user_data = mongo.db.users.find_one({'email': email})
        
        if not UserModel.verify_is_confirmed(email) and user_data['code'] == code:
            return True
        else:
            return False
        

    
    @staticmethod
    def turn_confirmed(email):
        """Alterar o status de um usuário para confirmado"""
        mongo.db.users.update_one({'email': email}, {'$set': {'is_confirmed': True}})
        mongo.db.users.update_one({'email': email}, {'$unset': {'code':''}})
        
    @staticmethod
    def generate_code(email):
        code = ''.join(random.choices(string.digits, k=6))
        mongo.db.users.update_one({'email': email}, {'$set': {'code':code}})
        return code
        
        

    def update_password(self, user_id,  new_password):
        user_data = delf.find_by_id(user_id)
        
        if user_data:
            return UserModel(**user_data)
        return None
    
        mongo.db.users.update_one({'id': user_data.id}, {'$set': {'password': new_password}})

    def to_dict(self):
        """Converte o objeto UserModel para dicionário"""
        return {
            '_id': self.id,
            'name': self.name,
            'email': self.email,
            'password': self.password
        }
