from fastapi import APIRouter
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.referral import Referral
from backend.app.models.wallet_history import WalletHistory
from backend.app.models.fraud_log import FraudLog
from backend.app.utils.level import get_vip_status

router = APIRouter()

@router.post("/referral/register")
def register_referral(inviter_telegram_id: str, invited_telegram_id: str, invited_username: str = None):
    db = SessionLocal()
    try:
        if inviter_telegram_id == invited_telegram_id:
            return {"error": "You cannot invite yourself"}

        inviter = db.query(User).filter(User.telegram_id == inviter_telegram_id).first()
        if not inviter:
            return {"error": "Inviter not found"}

        # 🔥 BLOQUEIO ANTI-FRAUDE
        blocked = db.query(FraudLog).filter(
            FraudLog.telegram_id == inviter_telegram_id,
            FraudLog.is_blocked == True
        ).first()

        if blocked:
            return {"error": "User blocked by anti-fraud system"}

        existing_invited = db.query(User).filter(User.telegram_id == invited_telegram_id).first()
        if existing_invited:
            return {"error": "Invited user already exists"}

        existing_referral = db.query(Referral).filter(
            Referral.invited_telegram_id == invited_telegram_id
        ).first()

        if existing_referral:
            return {"error": "Referral already registered"}

        base_reward = 100
        vip = get_vip_status(inviter.points_balance)
        multiplier = vip["multiplier"]
        final_reward = int(base_reward * multiplier)

        invited_user = User(
            telegram_id=invited_telegram_id,
            username=invited_username,
            display_name=invited_username,
            points_balance=0
        )

        referral = Referral(
            inviter_telegram_id=inviter_telegram_id,
            invited_telegram_id=invited_telegram_id,
            reward_points=final_reward
        )

        inviter.points_balance += final_reward

        history = WalletHistory(
            telegram_id=inviter_telegram_id,
            action_type="referral",
            amount=final_reward,
            description=f"Referral reward (x{multiplier})"
        )

        db.add(invited_user)
        db.add(referral)
        db.add(history)
        db.commit()
        db.refresh(inviter)

        return {
            "message": "Referral registered successfully",
            "final_reward": final_reward,
            "inviter_points_balance": inviter.points_balance
        }

    finally:
        db.close()