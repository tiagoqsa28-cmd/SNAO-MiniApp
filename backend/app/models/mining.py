from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime
from backend.app.database import Base

class Mining(Base):
    __tablename__ = "mining"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    started_at = Column(DateTime, nullable=True)
    last_claim_at = Column(DateTime, nullable=True)
    mined_amount = Column(Float, default=0.0)
    is_active = Column(Boolean, default=False)
    fast_pass_active = Column(Boolean, default=False)
    fast_pass_expires_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)