from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from backend.app.database import Base

class AdvancedMission(Base):
    __tablename__ = "advanced_missions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    mission_type = Column(String, nullable=False)
    question = Column(String, nullable=False)
    correct_answer = Column(String, nullable=True)
    reward_points = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)