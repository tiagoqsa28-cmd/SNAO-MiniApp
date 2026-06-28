from fastapi import APIRouter
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.wallet_history import WalletHistory
from backend.app.models.streak import Streak
from backend.app.models.vip import VIP
from backend.app.utils.level import get_user_level, get_multiplier_by_vip_level

router = APIRouter()

@router.get("/wallet/{telegram_id}")
def get_wallet(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            return {"error": "User not found"}

        history = (
            db.query(WalletHistory)
            .filter(WalletHistory.telegram_id == telegram_id)
            .order_by(WalletHistory.created_at.desc())
            .all()
        )

        streak = db.query(Streak).filter(Streak.telegram_id == telegram_id).first()

        vip = db.query(VIP).filter(
            VIP.telegram_id == telegram_id,
            VIP.is_active == True
        ).first()

        vip_level = vip.level if vip else None
        multiplier = get_multiplier_by_vip_level(vip_level)

        return {
            "telegram_id": user.telegram_id,
            "username": user.username,
            "points_balance": user.points_balance,
            "level": get_user_level(user.points_balance),
            "vip": True if vip else False,
            "vip_level": vip_level,
            "reward_multiplier": multiplier,
            "current_streak": streak.current_streak if streak else 0,
            "best_streak": streak.best_streak if streak else 0,
            "history": [
                {
                    "type": item.action_type,
                    "amount": item.amount,
                    "description": item.description,
                    "created_at": item.created_at
                }
                for item in history
            ]
        }

    finally:
        db.close()


@router.post("/wallet/history/add")
def add_wallet_history(telegram_id: str, action_type: str, amount: int, description: str = None):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            return {"error": "User not found"}

        history = WalletHistory(
            telegram_id=telegram_id,
            action_type=action_type,
            amount=amount,
            description=description
        )

        db.add(history)
        db.commit()

        return {
            "message": "History added successfully",
            "telegram_id": telegram_id,
            "action_type": action_type,
            "amount": amount,
            "description": description
        }

    finally:
        db.close()