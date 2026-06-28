from fastapi import APIRouter
from backend.app.models.user import User
from backend.app.database import SessionLocal

router = APIRouter()

@router.post("/create-user")
def create_user(telegram_id: str, username: str = None):
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if existing_user:
            return {
                "message": "User already exists",
                "id": existing_user.id,
                "telegram_id": existing_user.telegram_id,
                "username": existing_user.username,
            }

        user = User(
            telegram_id=telegram_id,
            username=username,
            display_name=username,
            points_balance=0
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "message": "User created successfully",
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "points_balance": user.points_balance
        }
    finally:
        db.close()