from fastapi import APIRouter
from datetime import datetime, timedelta
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.mining import Mining
from backend.app.models.vip import VIP
from backend.app.models.wallet_history import WalletHistory

router = APIRouter()

MINING_REWARDS = {
    "none": 1.0,
    "silver": 2.0,
    "gold": 5.0,
    "diamond": 10.0
}


def get_cycle_hours(mining: Mining):
    if mining.fast_pass_active and mining.fast_pass_expires_at and mining.fast_pass_expires_at > datetime.utcnow():
        return 6
    return 12


def get_reward_amount(vip_level):
    if not vip_level:
        return MINING_REWARDS["none"]

    return MINING_REWARDS.get(vip_level.lower(), 1.0)


@router.post("/mining/start")
def start_mining(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            return {"error": "User not found"}

        mining = db.query(Mining).filter(Mining.telegram_id == telegram_id).first()

        if not mining:
            mining = Mining(telegram_id=telegram_id)
            db.add(mining)
            db.commit()
            db.refresh(mining)

        if mining.is_active:
            return {"error": "Mining already active"}

        now = datetime.utcnow()

        mining.started_at = now
        mining.updated_at = now
        mining.mined_amount = 0.0
        mining.is_active = True

        db.commit()

        return {
            "message": "Mining started",
            "telegram_id": telegram_id,
            "cycle_hours": get_cycle_hours(mining)
        }

    finally:
        db.close()


@router.get("/mining/status/{telegram_id}")
def mining_status(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            return {"error": "User not found"}

        mining = db.query(Mining).filter(Mining.telegram_id == telegram_id).first()

        if not mining:
            return {
                "telegram_id": telegram_id,
                "is_active": False,
                "mined_amount": 0,
                "progress": 0,
                "can_claim": False
            }

        vip = db.query(VIP).filter(
            VIP.telegram_id == telegram_id,
            VIP.is_active == True
        ).first()

        vip_level = vip.level if vip else None
        total_reward = get_reward_amount(vip_level)
        cycle_hours = get_cycle_hours(mining)

        if not mining.is_active or not mining.started_at:
            return {
                "telegram_id": telegram_id,
                "is_active": False,
                "fast_pass_active": mining.fast_pass_active,
                "fast_pass_expires_at": mining.fast_pass_expires_at,
                "cycle_hours": cycle_hours,
                "total_reward": total_reward,
                "mined_amount": 0,
                "progress": 0,
                "can_claim": False
            }

        now = datetime.utcnow()
        elapsed_seconds = (now - mining.started_at).total_seconds()
        cycle_seconds = cycle_hours * 3600

        progress = min(elapsed_seconds / cycle_seconds, 1)
        mined_amount = round(total_reward * progress, 6)
        can_claim = progress >= 1

        mining.mined_amount = mined_amount
        mining.updated_at = now
        db.commit()

        return {
            "telegram_id": telegram_id,
            "is_active": mining.is_active,
            "fast_pass_active": mining.fast_pass_active,
            "fast_pass_expires_at": mining.fast_pass_expires_at,
            "cycle_hours": cycle_hours,
            "vip_level": vip_level,
            "total_reward": total_reward,
            "mined_amount": mined_amount,
            "progress": round(progress * 100, 2),
            "can_claim": can_claim
        }

    finally:
        db.close()


@router.post("/mining/claim")
def claim_mining(telegram_id: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            return {"error": "User not found"}

        mining = db.query(Mining).filter(Mining.telegram_id == telegram_id).first()

        if not mining or not mining.is_active:
            return {"error": "No active mining"}

        vip = db.query(VIP).filter(
            VIP.telegram_id == telegram_id,
            VIP.is_active == True
        ).first()

        vip_level = vip.level if vip else None
        total_reward = get_reward_amount(vip_level)
        cycle_hours = get_cycle_hours(mining)

        now = datetime.utcnow()
        elapsed_seconds = (now - mining.started_at).total_seconds()
        cycle_seconds = cycle_hours * 3600

        if elapsed_seconds < cycle_seconds:
            return {"error": "Mining cycle not completed yet"}

        user.points_balance += total_reward

        history = WalletHistory(
            telegram_id=telegram_id,
            action_type="mining",
            amount=int(total_reward),
            description=f"Mining reward: {total_reward} SNAO"
        )

        mining.is_active = False
        mining.mined_amount = total_reward
        mining.last_claim_at = now
        mining.updated_at = now

        db.add(history)
        db.commit()
        db.refresh(user)

        return {
            "message": "Mining claimed",
            "reward": total_reward,
            "points_balance": user.points_balance
        }

    finally:
        db.close()


@router.post("/mining/fast-pass/activate")
def activate_fast_pass(telegram_id: str, months: int = 1):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            return {"error": "User not found"}

        mining = db.query(Mining).filter(Mining.telegram_id == telegram_id).first()

        if not mining:
            mining = Mining(telegram_id=telegram_id)
            db.add(mining)
            db.commit()
            db.refresh(mining)

        mining.fast_pass_active = True
        mining.fast_pass_expires_at = datetime.utcnow() + timedelta(days=30 * months)
        mining.updated_at = datetime.utcnow()

        db.commit()

        return {
            "message": "Fast Mining Pass activated",
            "telegram_id": telegram_id,
            "valid_months": months,
            "expires_at": mining.fast_pass_expires_at,
            "cycle_hours": 6
        }

    finally:
        db.close()