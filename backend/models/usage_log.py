from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from backend.database import Base

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    public_ip = Column(String)
    user_agent = Column(String)
    browser = Column(String)
    browser_version = Column(String)
    os = Column(String)
    os_version = Column(String)
