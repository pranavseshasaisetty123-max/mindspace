from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class AIReflection(Base):
    __tablename__ = "ai_reflections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    journal_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=False)
    detected_patterns = Column(Text, nullable=False)  # Stored as a raw text string list or JSON payload
    reflection_question = Column(Text, nullable=False)
    generated_at = Column(DateTime, server_default=func.now(), nullable=False)
    model_used = Column(String(50), nullable=False)

    # Relationships
    journal = relationship("JournalEntry", back_populates="reflection")
