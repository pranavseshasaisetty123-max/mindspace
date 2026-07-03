from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
import re

class UserSettingsResponse(BaseModel):
    reminder_enabled: bool
    reminder_time: str
    timezone: str
    theme: str

    model_config = ConfigDict(from_attributes=True)

class UserSettingsUpdate(BaseModel):
    reminder_enabled: Optional[bool] = None
    reminder_time: Optional[str] = None
    timezone: Optional[str] = None
    theme: Optional[str] = None

    @field_validator("reminder_time")
    @classmethod
    def validate_time_format(cls, v):
        if v is not None:
            # Ensure time matches HH:MM in 24h format
            if not re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", v):
                raise ValueError("reminder_time must be in HH:MM 24-hour format")
        return v
