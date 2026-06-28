from fastapi import APIRouter
from backend.app.models.user import User
from backend.app.models.wallet_history import WalletHistory
from backend.app.database import SessionLocal

router = APIRouter()

@router.post("/add-points")
def add_points(telegram_id: str, amount: int, description: str = "Manual points added"):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            return {"error": "User not found"}

        user.points_balance += amount

        history = WalletHistory(
            telegram_id=telegram_id,
            action_type="manual_points",
            amount=amount,
            description=description
        )

        db.add(history)
        db.commit()
        db.refresh(user)

        return {
            "message": "Points added successfully",
            "telegram_id": user.telegram_id,
            "username": user.username,
            "points_added": amount,
            "points_balance": user.points_balance
        }

    finally:
        db.close()