from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from app.database import Base


class RateLimit(Base):
    __tablename__ = "rate_limits"
    
    id = Column(String(36), primary_key=True)
    identifier = Column(String(255), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    count = Column(Integer, default=0, nullable=False)
    reset_at = Column(DateTime, nullable=False, index=True)
