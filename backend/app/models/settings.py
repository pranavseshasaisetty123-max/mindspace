from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    reminder_enabled = Column(Boolean, default=False, nullable=False)
    reminder_time = Column(String(5), default="21:00", nullable=False)  # HH:MM format
    timezone = Column(String(50), default="UTC", nullable=False)
    theme = Column(String(20), default="dark", nullable=False)

    # Relationships
    user = relationship("User", back_populates="settings")
