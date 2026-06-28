from fastapi import APIRouter
from datetime import datetime
from backend.app.database import SessionLocal
from backend.app.models.user import User

router = APIRouter()

def get_week_key():
    now = datetime.utcnow()
    year, week, _ = now.isocalendar()
    return f"{year}-W{week}"


@router.get("/weekly/ranking")
def weekly_ranking(limit: int = 10):
    db = SessionLocal()
    try:
        users = (
            db.query(User)
            .order_by(User.points_balance.desc())
            .limit(limit)
            .all()
        )

        return {
            "week": get_week_key(),
            "ranking": [
                {
                    "position": index + 1,
                    "telegram_id": user.telegram_id,
                    "username": user.username,
                    "points": user.points_balance
                }
                for index, user in enumerate(users)
            ]
        }

    finally:
        db.close()