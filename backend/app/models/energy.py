from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.app.database import Base

class Energy(Base):
    __tablename__ = "energy"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    energy_left = Column(Integer, default=5)
    max_energy = Column(Integer, default=5)
    last_reset_date = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)