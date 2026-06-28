from sqlalchemy import Column, Integer, String, Boolean
from backend.app.database import Base

class VIP(Base):
    __tablename__ = "vip"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, index=True, nullable=False)
    level = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)