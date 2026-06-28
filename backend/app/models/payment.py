from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from backend.app.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, index=True, nullable=False)
    plan = Column(String, nullable=False)
    amount_usdt = Column(Float, nullable=False)
    network = Column(String, default="BEP20")
    wallet_address = Column(String, nullable=False)
    tx_hash = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, confirmed, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)