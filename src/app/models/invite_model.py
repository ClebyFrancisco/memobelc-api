from src.app import mongo
from bson import ObjectId
import string
import random
from datetime import datetime, timezone


class InviteModel:
    """Modelo para gerenciar convites de usuários"""

    @staticmethod
    def generate_invite_code():
        """Gera um código único de convite"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

    @staticmethod
    def create_invite_by_email(inviter_id, email):
        """Cria um convite por email"""
        invite_code = InviteModel.generate_invite_code()
        
        invite_data = {
            'inviter_id': ObjectId(inviter_id),
            'invite_code': invite_code,
            'invited_email': email.lower(),
            'invited_by_link': False,
            'status': 'pending',  # pending, accepted
            'created_at': datetime.now(timezone.utc),
            'accepted_at': None
        }
        
        result = mongo.db.invites.insert_one(invite_data)
        return str(result.inserted_id), invite_code

    @staticmethod
    def create_invite_by_link(inviter_id):
        """Cria um convite por link (gera código único)"""
        invite_code = InviteModel.generate_invite_code()
        
        # Verifica se o código já existe
        while mongo.db.invites.find_one({'invite_code': invite_code}):
            invite_code = InviteModel.generate_invite_code()
        
        invite_data = {
            'inviter_id': ObjectId(inviter_id),
            'invite_code': invite_code,
            'invited_email': None,
            'invited_by_link': True,
            'status': 'pending',
            'created_at': datetime.now(timezone.utc),
            'accepted_at': None
        }
        
        result = mongo.db.invites.insert_one(invite_data)
        return str(result.inserted_id), invite_code

    @staticmethod
    def get_invite_by_code(invite_code):
        """Busca um convite pelo código"""
        invite_data = mongo.db.invites.find_one({'invite_code': invite_code})
        if invite_data:
            invite_data['_id'] = str(invite_data['_id'])
            invite_data['inviter_id'] = str(invite_data['inviter_id'])
            return invite_data
        return None

    @staticmethod
    def accept_invite(invite_code, user_id, user_email):
        """Marca um convite como aceito quando o usuário se registra"""
        invite = InviteModel.get_invite_by_code(invite_code)
        if not invite:
            return False
        
        # Atualiza o convite
        mongo.db.invites.update_one(
            {'invite_code': invite_code},
            {
                '$set': {
                    'status': 'accepted',
                    'accepted_at': datetime.now(timezone.utc),
                    'invited_user_id': ObjectId(user_id),
                    'invited_email': user_email.lower()
                }
            }
        )
        
        # Adiciona o convidado à lista de amigos do usuário que convidou
        inviter_id = invite['inviter_id']
        mongo.db.users.update_one(
            {'_id': ObjectId(inviter_id)},
            {
                '$addToSet': {
                    'invited_friends': {
                        'user_id': ObjectId(user_id),
                        'email': user_email.lower(),
                        'invite_code': invite_code,
                        'invited_at': invite['created_at'],
                        'accepted_at': datetime.now(timezone.utc),
                        'status': 'accepted'
                    }
                }
            }
        )
        
        return True

    @staticmethod
    def get_user_invites(user_id):
        """Retorna todos os convites feitos por um usuário"""
        try:
            invites = list(mongo.db.invites.find({'inviter_id': ObjectId(user_id)}))
            
            result = []
            for invite in invites:
                invite_data = {
                    '_id': str(invite['_id']),
                    'invite_code': invite.get('invite_code'),
                    'invited_email': invite.get('invited_email'),
                    'invited_by_link': invite.get('invited_by_link', False),
                    'status': invite.get('status', 'pending'),
                    'created_at': invite.get('created_at'),
                    'accepted_at': invite.get('accepted_at'),
                    'invited_user_id': str(invite.get('invited_user_id')) if invite.get('invited_user_id') else None
                }
                result.append(invite_data)
            
            return result
        except Exception as e:
            print(f"Erro ao buscar convites: {str(e)}")
            return []

    @staticmethod
    def get_user_invited_friends(user_id):
        """Retorna a lista de amigos convidados de um usuário (do campo invited_friends)"""
        try:
            user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            if not user:
                return []
            
            invited_friends = user.get('invited_friends', [])
            
            # Converte ObjectId para string
            result = []
            for friend in invited_friends:
                friend_data = {
                    'user_id': str(friend.get('user_id')) if friend.get('user_id') else None,
                    'email': friend.get('email'),
                    'invite_code': friend.get('invite_code'),
                    'invited_at': friend.get('invited_at'),
                    'accepted_at': friend.get('accepted_at'),
                    'status': friend.get('status', 'pending')
                }
                result.append(friend_data)
            
            return result
        except Exception as e:
            print(f"Erro ao buscar amigos convidados: {str(e)}")
            return []

    @staticmethod
    def update_invite_status_by_email(email, status='accepted'):
        """Atualiza o status de um convite por email quando o usuário se registra"""
        # Busca convites pendentes para este email
        invite = mongo.db.invites.find_one({
            'invited_email': email.lower(),
            'status': 'pending'
        })
        
        if invite:
            inviter_id = str(invite['inviter_id'])
            
            # Busca o user_id do convidado pelo email
            user = mongo.db.users.find_one({'email': email.lower()})
            if user:
                user_id = str(user['_id'])
                
                # Atualiza o convite
                mongo.db.invites.update_one(
                    {'_id': invite['_id']},
                    {
                        '$set': {
                            'status': status,
                            'accepted_at': datetime.now(timezone.utc),
                            'invited_user_id': ObjectId(user_id)
                        }
                    }
                )
                
                # Adiciona à lista de amigos convidados
                mongo.db.users.update_one(
                    {'_id': ObjectId(inviter_id)},
                    {
                        '$addToSet': {
                            'invited_friends': {
                                'user_id': ObjectId(user_id),
                                'email': email.lower(),
                                'invite_code': invite.get('invite_code'),
                                'invited_at': invite.get('created_at'),
                                'accepted_at': datetime.now(timezone.utc),
                                'status': status
                            }
                        }
                    }
                )
                
                return True
        
        return False

