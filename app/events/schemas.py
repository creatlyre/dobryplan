from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    start_at: datetime
    end_at: datetime
    timezone: str = "UTC"
    rrule: Optional[str] = None
    visibility: Literal["shared", "private"] = "shared"
    reminder_minutes: Optional[int] = None
    reminder_minutes_list: Optional[List[int]] = None

    @field_validator("reminder_minutes_list")
    @classmethod
    def validate_reminder_list(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None:
            for m in v:
                if m < 0:
                    raise ValueError("reminder minutes must be non-negative")
                if m > 40320:  # 4 weeks
                    raise ValueError("reminder minutes cannot exceed 40320 (4 weeks)")
        return v


class EventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    timezone: Optional[str] = None
    rrule: Optional[str] = None
    visibility: Optional[Literal["shared", "private"]] = None
    reminder_minutes: Optional[int] = None
    reminder_minutes_list: Optional[List[int]] = None


class EventResponse(BaseModel):
    id: str
    calendar_id: str
    created_by_user_id: Optional[str]
    title: str
    description: Optional[str]
    start_at: datetime
    end_at: datetime
    timezone: str
    is_deleted: bool
    rrule: Optional[str] = None
    visibility: str = "shared"
    reminder_minutes: Optional[int] = None
    reminder_minutes_list: List[int] = []

    model_config = {"from_attributes": True}
