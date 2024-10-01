from src.app import mongo

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
        return mongo.db.users.insert_one(user_data)

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
        print(user_data)
        if user_data and user_data['is_confirmed']:
            return True
        else:
            return False

    
    @staticmethod
    def turn_confirmed(email):
        """Alterar o status de um usuário para confirmado"""
        mongo.db.users.update_one({'email': email}, {'$set': {'is_confirmed': True}})
        
        

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
