from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List

class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)

class JournalBase(BaseModel):
    title: str = Field(..., max_length=255, description="Title of the journal entry")
    content: str = Field(..., description="Markdown content of the journal entry")
    mood: int = Field(..., ge=1, le=5, description="Mood rating from 1 to 5")
    stress_level: int = Field(..., ge=1, le=5, description="Stress rating from 1 to 5")
    energy_level: int = Field(..., ge=1, le=5, description="Energy rating from 1 to 5")
    sleep_hours: float = Field(..., ge=0.0, description="Sleep duration in hours")

class JournalCreate(JournalBase):
    tags: List[str] = Field(default=[], description="List of tags to associate with the journal entry")

class JournalUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    mood: Optional[int] = Field(None, ge=1, le=5)
    stress_level: Optional[int] = Field(None, ge=1, le=5)
    energy_level: Optional[int] = Field(None, ge=1, le=5)
    sleep_hours: Optional[float] = Field(None, ge=0.0)
    tags: Optional[List[str]] = Field(None, description="List of tags. Replaces existing tags if provided.")

class JournalResponse(JournalBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    tags: List[TagResponse] = []

    model_config = ConfigDict(from_attributes=True)
