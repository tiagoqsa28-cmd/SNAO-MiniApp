from fastapi import APIRouter
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.fraud_log import FraudLog

router = APIRouter()

@router.post("/anti-fraud/flag")
def flag_user(telegram_id: str, reason: str, block: bool = False):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            return {"error": "User not found"}

        fraud_log = FraudLog(
            telegram_id=telegram_id,
            reason=reason,
            is_blocked=block
        )

        db.add(fraud_log)
        db.commit()
        db.refresh(fraud_log)

        return {
            "message": "User flagged successfully",
            "telegram_id": telegram_id,
            "reason": reason,
            "blocked": block
        }

    finally:
        db.close()


@router.get("/anti-fraud/status/{telegram_id}")
def fraud_status(telegram_id: str):
    db = SessionLocal()
    try:
        logs = (
            db.query(FraudLog)
            .filter(FraudLog.telegram_id == telegram_id)
            .order_by(FraudLog.created_at.desc())
            .all()
        )

        blocked = any(log.is_blocked for log in logs)

        return {
            "telegram_id": telegram_id,
            "is_flagged": len(logs) > 0,
            "is_blocked": blocked,
            "total_flags": len(logs),
            "logs": [
                {
                    "reason": log.reason,
                    "blocked": log.is_blocked,
                    "created_at": log.created_at
                }
                for log in logs
            ]
        }

    finally:
        db.close()