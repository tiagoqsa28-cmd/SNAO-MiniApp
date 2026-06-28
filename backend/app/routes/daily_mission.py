from fastapi import APIRouter
from datetime import datetime
from backend.app.database import SessionLocal
from backend.app.models.daily_mission import DailyMission

router = APIRouter()

@router.get("/daily-mission")
def get_daily_mission():
    db = SessionLocal()
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")

        mission = db.query(DailyMission).filter(DailyMission.date == today).first()

        if not mission:
            mission = DailyMission(
                title="Complete 1 task today",
                reward_points=100,
                date=today
            )
            db.add(mission)
            db.commit()
            db.refresh(mission)

        return {
            "title": mission.title,
            "reward_points": mission.reward_points,
            "date": mission.date
        }

    finally:
        db.close()