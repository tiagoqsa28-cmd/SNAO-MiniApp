from fastapi import APIRouter
from datetime import datetime
from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.task import Task
from backend.app.models.user_task import UserTask
from backend.app.models.wallet_history import WalletHistory
from backend.app.models.fraud_log import FraudLog
from backend.app.models.energy import Energy
from backend.app.models.daily_combo import DailyCombo
from backend.app.models.vip import VIP
from backend.app.utils.level import get_multiplier_by_vip_level

router = APIRouter()


@router.post("/tasks/create")
def create_task(title: str, reward_points: int, task_type: str, description: str = None, target_url: str = None):
    db = SessionLocal()
    try:
        task = Task(
            title=title,
            description=description,
            reward_points=reward_points,
            task_type=task_type,
            target_url=target_url,
            is_active=True
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        return {"message": "Task created", "task_id": task.id}

    finally:
        db.close()


@router.post("/tasks/complete")
def complete_task(telegram_id: str, task_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            return {"error": "User not found"}

        vip = db.query(VIP).filter(
            VIP.telegram_id == telegram_id,
            VIP.is_active == True
        ).first()

        vip_level = vip.level if vip else None
        multiplier = get_multiplier_by_vip_level(vip_level)

        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"error": "Task not found"}

        existing = db.query(UserTask).filter(
            UserTask.telegram_id == telegram_id,
            UserTask.task_id == task_id
        ).first()

        if existing and existing.completed:
            return {"error": "Task already completed"}

        user_task = existing or UserTask(
            telegram_id=telegram_id,
            task_id=task_id
        )

        user_task.completed = True
        user_task.completed_at = datetime.utcnow()

        final_reward = int(task.reward_points * multiplier)
        user.points_balance += final_reward

        db.add(WalletHistory(
            telegram_id=telegram_id,
            action_type="task",
            amount=final_reward,
            description=f"Task reward (VIP x{multiplier})"
        ))

        if not existing:
            db.add(user_task)

        db.commit()
        db.refresh(user)

        return {
            "reward": final_reward,
            "multiplier": multiplier,
            "points_balance": user.points_balance
        }

    finally:
        db.close()