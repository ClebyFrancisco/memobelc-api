"""Model for tracking user study streaks (consecutive days)."""

from datetime import datetime, timedelta, timezone
from bson import ObjectId
from src.app import mongo


class UserStreakModel:
    """Model for tracking consecutive study days."""

    @staticmethod
    def record_study_day(user_id: str):
        """Registra um dia de estudo para o usuário. Se já foi registrado hoje, não faz nada."""
        today = datetime.now(timezone.utc).date()
        user_obj_id = ObjectId(user_id)

        # Verifica se já existe registro para hoje
        existing = mongo.db.user_streaks.find_one({
            "user_id": user_obj_id,
            "date": today.isoformat()
        })

        if not existing:
            # Insere novo registro para hoje
            mongo.db.user_streaks.insert_one({
                "user_id": user_obj_id,
                "date": today.isoformat(),
                "created_at": datetime.now(timezone.utc)
            })

    @staticmethod
    def get_streak_info(user_id: str) -> dict:
        """Retorna informações sobre o streak atual do usuário.
        
        Returns:
            dict com:
                - current_streak: int (dias consecutivos)
                - last_study_date: str ou None (última data estudada)
                - week_study_days: list[bool] (7 dias da semana, True se estudou)
        """
        user_obj_id = ObjectId(user_id)
        
        # Busca todos os registros de estudo do usuário
        all_studies = list(mongo.db.user_streaks.find(
            {"user_id": user_obj_id},
            sort=[("date", -1)]
        ))

        if not all_studies:
            return {
                "current_streak": 0,
                "last_study_date": None,
                "week_study_days": [False] * 7
            }

        # Converte datas de string ISO para date
        study_dates = set()
        for study in all_studies:
            date_str = study.get("date")
            if date_str:
                from datetime import date
                study_dates.add(date.fromisoformat(date_str))

        today = datetime.now(timezone.utc).date()
        last_study_date = max(study_dates) if study_dates else None

        # Calcula streak atual (dias consecutivos até hoje)
        current_streak = 0
        check_date = today

        while check_date in study_dates:
            current_streak += 1
            check_date -= timedelta(days=1)

        # Calcula dias da semana atual (últimos 7 dias, começando de hoje)
        week_study_days = []
        for i in range(6, -1, -1):  # 6 dias atrás até hoje (7 dias)
            day_check = today - timedelta(days=i)
            week_study_days.append(day_check in study_dates)

        return {
            "current_streak": current_streak,
            "last_study_date": last_study_date.isoformat() if last_study_date else None,
            "week_study_days": week_study_days
        }

