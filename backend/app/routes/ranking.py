from fastapi import APIRouter
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.utils.level import get_user_level

router = APIRouter()

@router.get("/ranking")
def get_ranking(limit: int = 10):
    db = SessionLocal()
    try:
        users = (
            db.query(User)
            .order_by(User.points_balance.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "position": index + 1,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "display_name": user.display_name,
                "points": user.points_balance,
                "level": get_user_level(user.points_balance)
            }
            for index, user in enumerate(users)
        ]

    finally:
        db.close()