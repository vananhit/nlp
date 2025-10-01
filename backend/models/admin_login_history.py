from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from backend.database import Base
from datetime import datetime
import pytz

# Helper function to get current time in Vietnam timezone
def get_vn_time():
    return datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))

class AdminLoginHistory(Base):
    __tablename__ = "admin_login_history"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    os = Column(String, nullable=True)
    os_version = Column(String, nullable=True)
    browser = Column(String, nullable=True)
    browser_version = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=get_vn_time)
