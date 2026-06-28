from fastapi import APIRouter
from datetime import datetime, timedelta
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.wallet_history import WalletHistory
from backend.app.models.fraud_log import FraudLog
from backend.app.models.streak import Streak
from backend.app.utils.level import get_vip_status

router = APIRouter()

@router.post("/daily")
def daily_reward(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            return {"error": "User not found"}

        blocked = (
            db.query(FraudLog)
            .filter(
                FraudLog.telegram_id == telegram_id,
                FraudLog.is_blocked == True
            )
            .first()
        )

        if blocked:
            return {"error": "User blocked by anti-fraud system"}

        now = datetime.utcnow()

        streak = db.query(Streak).filter(Streak.telegram_id == telegram_id).first()

        if not streak:
            streak = Streak(
                telegram_id=telegram_id,
                current_streak=0,
                best_streak=0,
                last_claim_at=None
            )
            db.add(streak)
            db.commit()
            db.refresh(streak)

        if streak.last_claim_at and (now - streak.last_claim_at) < timedelta(hours=24):
            return {"error": "Daily reward already claimed"}

        if streak.last_claim_at and (now - streak.last_claim_at) <= timedelta(hours=48):
            streak.current_streak += 1
        else:
            streak.current_streak = 1

        if streak.current_streak > streak.best_streak:
            streak.best_streak = streak.current_streak

        streak.last_claim_at = now
        streak.updated_at = now

        base_reward = 50
        streak_bonus = streak.current_streak * 5

        vip = get_vip_status(user.points_balance)
        multiplier = vip["multiplier"]

        final_reward = int((base_reward + streak_bonus) * multiplier)

        user.points_balance += final_reward

        history = WalletHistory(
            telegram_id=telegram_id,
            action_type="daily",
            amount=final_reward,
            description=f"Daily reward + streak {streak.current_streak} days (x{multiplier})"
        )

        db.add(history)
        db.commit()
        db.refresh(user)
        db.refresh(streak)

        return {
            "message": "Daily reward claimed",
            "base_reward": base_reward,
            "streak_days": streak.current_streak,
            "best_streak": streak.best_streak,
            "streak_bonus": streak_bonus,
            "multiplier": multiplier,
            "final_reward": final_reward,
            "points_balance": user.points_balance
        }

    finally:
        db.close()