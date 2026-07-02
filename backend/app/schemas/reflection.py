import json
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import List

class AIReflectionResponse(BaseModel):
    id: int
    journal_id: int
    summary: str
    detected_patterns: List[str]
    reflection_question: str
    generated_at: datetime
    model_used: str
    is_outdated: bool = False

    model_config = ConfigDict(from_attributes=True)

    @field_validator("detected_patterns", mode="before")
    @classmethod
    def parse_patterns(cls, v):
        """Parse database string (JSON list or comma-separated list) into list of strings."""
        if isinstance(v, str):
            try:
                # Try parsing as a JSON array first
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed]
            except Exception:
                pass
            # Fallback to comma separated
            return [x.strip() for x in v.split(",") if x.strip()]
        return v
