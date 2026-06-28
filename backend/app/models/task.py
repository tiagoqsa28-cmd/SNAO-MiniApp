from sqlalchemy import Column, Integer, String, Boolean
from backend.app.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    reward_points = Column(Integer, default=0)
    task_type = Column(String, nullable=False)
    target_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)