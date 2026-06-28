from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.app.database import Base

class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    inviter_telegram_id = Column(String, index=True, nullable=False)
    invited_telegram_id = Column(String, unique=True, index=True, nullable=False)
    reward_points = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)