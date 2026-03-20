from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class User:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    name: str = ""
    google_id: str | None = None
    google_access_token: str | None = None
    google_refresh_token: str | None = None
    google_token_expiry: datetime | None = None
    calendar_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_login: datetime | None = None


@dataclass
class Calendar:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    timezone: str = "UTC"
    owner_user_id: str | None = None
    google_calendar_id: str | None = None
    last_sync_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class CalendarInvitation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str = ""
    invited_email: str = ""
    inviter_user_id: str | None = None
    status: str = "pending"
    created_at: datetime | None = None
    expires_at: datetime | None = None


@dataclass
class Event:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str = ""
    created_by_user_id: str | None = None
    title: str = ""
    description: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    timezone: str = "UTC"
    rrule: str | None = None
    google_event_id: str | None = None
    google_sync_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_edited_by_user_id: str | None = None
    is_deleted: bool = False
    visibility: str = "shared"
    reminder_minutes: int | None = None
    reminder_minutes_list: list[int] = field(default_factory=list)

    @property
    def effective_reminders(self) -> list[int]:
        """Return reminders: use list if set, else single reminder, else empty."""
        if self.reminder_minutes_list:
            return self.reminder_minutes_list
        if self.reminder_minutes is not None:
            return [self.reminder_minutes]
        return []
