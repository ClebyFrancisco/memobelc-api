from src.app import mongo
from src.app.provider.stripe import Stripe
import random
from bson import ObjectId
import string

class UserModel:
    def __init__(self, _id=None, name = None, email=None, password=None, collections=None, customer_id=None, **kwargs):
        self._id = str(_id) if _id else None
        self.name = name
        self.email = email
        self.password = password
        self.collections = collections or []
        self.customer_id = customer_id


    def save_to_db(self):
        """Salva o usuário no banco de dados MongoDB"""
        
        customer = Stripe.create_customer(self.email)
        user_data = {
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'is_confirmed': False,
            "collections": self.collections,
            "customer_id": customer.get('id')
        }
        
        
        mongo.db.users.insert_one(user_data)
        return True
    
    @staticmethod
    def add_collections_to_user(user_id, collection_ids):
        """Adiciona uma lista de collection IDs ao user especificado"""
        # Converte os IDs de decks para ObjectId
        collection_object_ids = [ObjectId(collection_id) for collection_id in collection_ids]
        
        # Atualiza o Collection, adicionando os IDs dos collections
        result = mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"collections": {"$each": collection_object_ids}}}
        )
        
        return result.modified_count > 0

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
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
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
        
        
    @staticmethod
    def update_password(user_id,  new_password):
        user = UserModel.find_by_id(user_id)
        
        if user:
            
            mongo.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {'password': new_password}}
            )
            return True
        
        return False
    
        

    def to_dict(self):
        """Converte o objeto UserModel para dicionário"""
        return {
            '_id': self._id,
            'name': self.name,
            'email': self.email,
            'collections': [str(ObjectId(collection_id)) for collection_id in self.collections],
            'customer_id':self.customer_id
        }
