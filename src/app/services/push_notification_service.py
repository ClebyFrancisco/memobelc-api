import requests

from src.app import mongo


class PushNotificationService:
    """Serviço responsável por enviar notificações push via Expo."""

    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

    @staticmethod
    def _get_tokens_for_user(user_id: str):
        cursor = mongo.db.push_notification.find({"user_id": str(user_id)})
        return [doc.get("push_token") for doc in cursor if doc.get("push_token")]

    @staticmethod
    def send_to_user(user_id: str, title: str, body: str, data=None) -> bool:
        tokens = PushNotificationService._get_tokens_for_user(user_id)
        if not tokens:
            return False

        messages = [
            {
                "to": token,
                "sound": "default",
                "title": title,
                "body": body,
                "data": data or {},
            }
            for token in tokens
        ]

        try:
            response = requests.post(
                PushNotificationService.EXPO_PUSH_URL, json=messages, timeout=5
            )
            return response.ok
        except Exception:
            # Em produção, seria interessante logar o erro
            return False


