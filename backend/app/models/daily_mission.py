from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.app.database import Base

class DailyMission(Base):
    __tablename__ = "daily_missions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    reward_points = Column(Integer, default=0)
    date = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)