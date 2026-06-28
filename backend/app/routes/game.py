from fastapi import APIRouter
from backend.app.database import SessionLocal

from backend.app.models.user import User
from backend.app.models.streak import Streak
from backend.app.models.energy import Energy
from backend.app.models.vip import VIP
from backend.app.models.advanced_mission import AdvancedMission
from backend.app.models.user_advanced_mission import UserAdvancedMission

from backend.app.utils.level import get_user_level, get_multiplier_by_vip_level

router = APIRouter()


@router.get("/game/{telegram_id}")
def get_game_state(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            return {"error": "User not found"}

        streak = db.query(Streak).filter(Streak.telegram_id == telegram_id).first()
        energy = db.query(Energy).filter(Energy.telegram_id == telegram_id).first()

        vip = db.query(VIP).filter(
            VIP.telegram_id == telegram_id,
            VIP.is_active == True
        ).first()

        vip_level = vip.level if vip else None
        multiplier = get_multiplier_by_vip_level(vip_level)

        # 🔥 MISSÕES DISPONÍVEIS
        missions = db.query(AdvancedMission).filter(
            AdvancedMission.is_active == True
        ).all()

        user_missions = db.query(UserAdvancedMission).filter(
            UserAdvancedMission.telegram_id == telegram_id
        ).all()

        completed_ids = [m.mission_id for m in user_missions]

        available_missions = [
            {
                "id": m.id,
                "title": m.title,
                "type": m.mission_type,
                "reward": m.reward_points,
                "question": m.question,
                "expires_at": m.expires_at
            }
            for m in missions if m.id not in completed_ids
        ]

        return {
            "player": {
                "telegram_id": user.telegram_id,
                "username": user.username,
                "points": user.points_balance,
                "level": get_user_level(user.points_balance)
            },

            "vip": {
                "active": True if vip else False,
                "level": vip_level,
                "multiplier": multiplier
            },

            "energy": {
                "current": energy.energy_left if energy else 5,
                "max": energy.max_energy if energy else 5
            },

            "streak": {
                "current": streak.current_streak if streak else 0,
                "best": streak.best_streak if streak else 0
            },

            "missions": {
                "available": available_missions,
                "completed": len(completed_ids)
            },

            "game_status": {
                "rank_enabled": True,
                "missions_enabled": True,
                "advanced_missions_enabled": True
            }
        }

    finally:
        db.close()