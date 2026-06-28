from fastapi import APIRouter
from datetime import datetime, timedelta
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.advanced_mission import AdvancedMission
from backend.app.models.user_advanced_mission import UserAdvancedMission
from backend.app.models.wallet_history import WalletHistory
from backend.app.models.fraud_log import FraudLog
from backend.app.models.vip import VIP
from backend.app.utils.level import get_multiplier_by_vip_level

router = APIRouter()


@router.post("/advanced-missions/create")
def create_advanced_mission(
    title: str,
    mission_type: str,
    question: str,
    correct_answer: str,
    reward_points: int,
    expires_in_hours: int = 24
):
    db = SessionLocal()
    try:
        mission = AdvancedMission(
            title=title,
            mission_type=mission_type,
            question=question,
            correct_answer=correct_answer.lower().strip(),
            reward_points=reward_points,
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours)
        )

        db.add(mission)
        db.commit()
        db.refresh(mission)

        return {
            "message": "Advanced mission created",
            "mission_id": mission.id,
            "title": mission.title,
            "mission_type": mission.mission_type,
            "reward_points": mission.reward_points,
            "expires_at": mission.expires_at
        }

    finally:
        db.close()


@router.get("/advanced-missions")
def list_advanced_missions():
    db = SessionLocal()
    try:
        now = datetime.utcnow()

        missions = db.query(AdvancedMission).filter(
            AdvancedMission.is_active == True
        ).all()

        return [
            {
                "id": mission.id,
                "title": mission.title,
                "mission_type": mission.mission_type,
                "question": mission.question,
                "reward_points": mission.reward_points,
                "expires_at": mission.expires_at,
                "expired": mission.expires_at is not None and mission.expires_at < now
            }
            for mission in missions
        ]

    finally:
        db.close()


@router.post("/advanced-missions/submit")
def submit_advanced_mission(telegram_id: str, mission_id: int, answer: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            return {"error": "User not found"}

        blocked = db.query(FraudLog).filter(
            FraudLog.telegram_id == telegram_id,
            FraudLog.is_blocked == True
        ).first()

        if blocked:
            return {"error": "User blocked by anti-fraud system"}

        mission = db.query(AdvancedMission).filter(
            AdvancedMission.id == mission_id,
            AdvancedMission.is_active == True
        ).first()

        if not mission:
            return {"error": "Mission not found"}

        now = datetime.utcnow()

        if mission.expires_at and mission.expires_at < now:
            return {"error": "Mission expired"}

        existing = db.query(UserAdvancedMission).filter(
            UserAdvancedMission.telegram_id == telegram_id,
            UserAdvancedMission.mission_id == mission_id
        ).first()

        if existing:
            return {"error": "Advanced mission already completed"}

        clean_answer = answer.lower().strip()
        correct = clean_answer == mission.correct_answer

        reward = 0
        multiplier = 1.0

        if correct:
            vip = db.query(VIP).filter(
                VIP.telegram_id == telegram_id,
                VIP.is_active == True
            ).first()

            vip_level = vip.level if vip else None
            multiplier = get_multiplier_by_vip_level(vip_level)

            reward = int(mission.reward_points * multiplier)
            user.points_balance += reward

            db.add(WalletHistory(
                telegram_id=telegram_id,
                action_type="advanced_mission",
                amount=reward,
                description=f"Advanced mission: {mission.title} (x{multiplier})"
            ))

        result = UserAdvancedMission(
            telegram_id=telegram_id,
            mission_id=mission_id,
            answer=answer,
            is_correct=correct,
            reward_points=reward
        )

        db.add(result)
        db.commit()
        db.refresh(user)

        return {
            "message": "Advanced mission submitted",
            "mission_id": mission_id,
            "correct": correct,
            "base_reward": mission.reward_points,
            "multiplier": multiplier,
            "reward_points": reward,
            "points_balance": user.points_balance
        }

    finally:
        db.close()