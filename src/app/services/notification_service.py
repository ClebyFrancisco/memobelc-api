from typing import Any, Dict, List, Optional
from bson import ObjectId
from datetime import datetime, timezone

from src.app import mongo
from src.app.models.notification.notification_model import NotificationModel
from src.app.models.user_model import UserModel
from src.app.models.user_progress_model import UserProgressModel
from src.app.models.classroom_model import ClassroomModel
from src.app.models.deck_model import DeckModel
from src.app.services.push_notification_service import PushNotificationService


class NotificationService:
    """Serviço central de notificações (internas + push)."""

    TYPE_DAILY_STUDY = "daily_study"
    TYPE_CLASSROOM_ADDED = "classroom_added"
    TYPE_NEW_CARDS = "new_cards"
    TYPE_TEACHER_CUSTOM = "teacher_custom"
    TYPE_ADMIN_CUSTOM = "admin_custom"

    # ---------- Funções utilitárias ----------
    @staticmethod
    def _create_and_push(
        user_id: str,
        notification_type: str,
        title: str,
        body: str,
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        data = {"title": title, "body": body}
        if extra_data:
            data.update(extra_data)

        # Cria registro interno
        NotificationModel.create(user_id=user_id, notification_type=notification_type, data=data)

        # Dispara push (se houver token cadastrado)
        PushNotificationService.send_to_user(user_id=user_id, title=title, body=body, data=extra_data or {})

    # ---------- API para controllers ----------
    @staticmethod
    def list_notifications(user_id: str):
        return NotificationModel.list_by_user(user_id)

    @staticmethod
    def count_unread(user_id: str) -> int:
        return NotificationModel.count_unread(user_id)

    @staticmethod
    def mark_as_read(user_id: str, notification_id: Optional[str] = None, mark_all: bool = False) -> int:
        return NotificationModel.mark_as_read(user_id=user_id, notification_id=notification_id, mark_all=mark_all)

    # ---------- Casos de uso específicos ----------
    @staticmethod
    def send_daily_study_notifications() -> Dict[str, Any]:
        """Envia notificação diária de estudos para usuários com cartas pendentes."""
        users_cursor = mongo.db.users.find({"is_confirmed": True})
        notified_users: List[str] = []

        for user in users_cursor:
            user_id = str(user["_id"])
            pending = UserProgressModel.count_pending_cards(user_id)

            if pending <= 0:
                continue

            # Garante no máximo UMA notificação "daily_study" por dia por usuário
            last = NotificationModel.find_last(
                user_id=user_id, notification_type=NotificationService.TYPE_DAILY_STUDY
            )
            if last and isinstance(last.get("created_at"), datetime):
                last_date = last["created_at"].date()
                today_date = datetime.now(timezone.utc).date()
                if last_date == today_date:
                    # Já foi enviada hoje, pula este usuário
                    continue

            title = "Hora de estudar!"
            body = f"Você tem {pending} cartas para revisar hoje. Vamos continuar sua jornada?"

            NotificationService._create_and_push(
                user_id=user_id,
                notification_type=NotificationService.TYPE_DAILY_STUDY,
                title=title,
                body=body,
                extra_data={"pending_cards": pending},
            )
            notified_users.append(user_id)

        return {"notified_users": notified_users}

    @staticmethod
    def notify_user_added_to_classroom(classroom_id: str, user_id: str):
        """Notifica o usuário quando for adicionado a uma classroom."""
        classroom = ClassroomModel.get_by_id(classroom_id)
        if not classroom:
            return

        title = "Você foi adicionado a uma turma!"
        body = f"Você agora faz parte da classroom '{classroom.get('name')}'."

        NotificationService._create_and_push(
            user_id=str(user_id),
            notification_type=NotificationService.TYPE_CLASSROOM_ADDED,
            title=title,
            body=body,
            extra_data={"classroom_id": classroom_id},
        )

    @staticmethod
    def notify_students_new_cards(deck_id: str, amount: int):
        """Notifica os alunos de classrooms quando um professor adiciona novas cartas em um deck."""
        deck = DeckModel.get_by_id(deck_id)
        if not deck:
            return

        # Descobre quais collections possuem esse deck
        collection_doc = mongo.db.collections.find_one({"decks": ObjectId(deck_id)})
        if not collection_doc:
            return

        collection_id = str(collection_doc["_id"])

        # Turmas que usam essa collection
        classrooms_cursor = mongo.db.classrooms.find({"collection": collection_doc["_id"]})

        for classroom in classrooms_cursor:
            classroom_id = str(classroom["_id"])
            students = classroom.get("students", [])

            for student_id in students:
                student_id_str = str(student_id)
                title = "Novas cartas disponíveis!"
                body = f"Foram adicionadas {amount} novas cartas no deck '{deck.get('name')}'."

                NotificationService._create_and_push(
                    user_id=student_id_str,
                    notification_type=NotificationService.TYPE_NEW_CARDS,
                    title=title,
                    body=body,
                    extra_data={
                        "deck_id": deck_id,
                        "classroom_id": classroom_id,
                        "collection_id": collection_id,
                    },
                )

    @staticmethod
    def teacher_custom_notification(teacher_id: str, classroom_id: str, title: str, body: str):
        """Professor envia uma notificação de texto livre para todos os alunos da turma."""
        classroom = ClassroomModel.get_by_id(classroom_id)
        if not classroom:
            return {"error": "Classroom not found"}

        students = classroom.get("students", [])
        for student in students:
            # no to_dict de ClassroomModel, students são dicionários com name/email
            # portanto precisamos buscar o user_id via email
            email = student.get("email")
            if not email:
                continue
            user = UserModel.find_by_email(email)
            if not user:
                continue

            NotificationService._create_and_push(
                user_id=user._id,
                notification_type=NotificationService.TYPE_TEACHER_CUSTOM,
                title=title,
                body=body,
                extra_data={"classroom_id": classroom_id, "from_teacher_id": teacher_id},
            )

        return {"sent_to": len(students)}

    @staticmethod
    def admin_custom_notification(admin_id: str, title: str, body: str, user_ids: Optional[List[str]] = None):
        """Admin envia notificação de texto livre.

        - Se user_ids for informado: envia apenas para esses usuários.
        - Caso contrário: envia para todos usuários confirmados.
        """
        if user_ids:
            target_users = [str(uid) for uid in user_ids]
        else:
            cursor = mongo.db.users.find({"is_confirmed": True})
            target_users = [str(u["_id"]) for u in cursor]

        for uid in target_users:
            NotificationService._create_and_push(
                user_id=uid,
                notification_type=NotificationService.TYPE_ADMIN_CUSTOM,
                title=title,
                body=body,
                extra_data={"from_admin_id": admin_id},
            )

        return {"sent_to": len(target_users)}


