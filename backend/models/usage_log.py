from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from backend.database import Base

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    request_data = Column(JSON)
