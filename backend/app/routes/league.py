from fastapi import APIRouter
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.utils.level import get_user_level

router = APIRouter()

@router.get("/league/ranking")
def league_ranking(level: str, limit: int = 10):
    db = SessionLocal()
    try:
        users = (
            db.query(User)
            .order_by(User.points_balance.desc())
            .all()
        )

        filtered_users = [
            user for user in users
            if get_user_level(user.points_balance).lower() == level.lower()
        ]

        return {
            "league": level,
            "ranking": [
                {
                    "position": index + 1,
                    "telegram_id": user.telegram_id,
                    "username": user.username,
                    "points": user.points_balance,
                    "level": get_user_level(user.points_balance)
                }
                for index, user in enumerate(filtered_users[:limit])
            ]
        }

    finally:
        db.close()