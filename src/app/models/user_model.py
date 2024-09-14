from src.app import mongo

class UserModel:
    def __init__(self, _id=None, name = None, email=None, password=None, **kwargs):
        self.id = str(_id)
        self.name = name
        self.email = email
        self.password = password

    def save_to_db(self):
        """Salva o usuário no banco de dados MongoDB"""
        user_data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': self.password
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
        user_data = mongo.db.users.find_one({'id': user_id})
        if user_data:
            return UserModel(**user_data)
        return None

    def update_password(self, new_password):
        """Atualiza a senha do usuário"""
        self.password = new_password
        mongo.db.users.update_one({'id': self.id}, {'$set': {'password': new_password}})

    def to_dict(self):
        """Converte o objeto UserModel para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': self.password
        }
