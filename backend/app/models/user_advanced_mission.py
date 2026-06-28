from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from backend.app.database import Base

class UserAdvancedMission(Base):
    __tablename__ = "user_advanced_missions"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, index=True, nullable=False)
    mission_id = Column(Integer, nullable=False)
    answer = Column(String, nullable=False)
    is_correct = Column(Boolean, default=False)
    reward_points = Column(Integer, default=0)
    completed_at = Column(DateTime, default=datetime.utcnow)