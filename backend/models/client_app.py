import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from backend.database import Base

class ClientApp(Base):
    __tablename__ = "client_apps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    client_id = Column(String, unique=True, index=True, nullable=False)
    hashed_secret = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
