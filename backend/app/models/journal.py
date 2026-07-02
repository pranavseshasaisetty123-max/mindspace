from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey, DateTime, func, Numeric, CheckConstraint
from sqlalchemy.orm import relationship
from app.database import Base

# Junction table mapping many-to-many relationship between entries and tags
journal_tags = Table(
    "journal_tags",
    Base.metadata,
    Column("entry_id", Integer, ForeignKey("journal_entries.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="tags")
    entries = relationship("JournalEntry", secondary=journal_tags, back_populates="tags")

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    
    # Metrics
    mood = Column(Integer, CheckConstraint("mood >= 1 AND mood <= 5"), nullable=False)
    stress_level = Column(Integer, CheckConstraint("stress_level >= 1 AND stress_level <= 5"), nullable=False)
    energy_level = Column(Integer, CheckConstraint("energy_level >= 1 AND energy_level <= 5"), nullable=False)
    sleep_hours = Column(Numeric(4, 2), CheckConstraint("sleep_hours >= 0.0"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True, index=True)  # Soft delete timestamp

    # Relationships
    user = relationship("User", back_populates="journals")
    tags = relationship("Tag", secondary=journal_tags, back_populates="entries")
