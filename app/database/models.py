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
class EventCategory:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str = ""
    name: str = ""
    color: str = "#6366f1"
    is_preset: bool = False
    sort_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


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
    category_id: str | None = None
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


@dataclass
class BudgetSettings:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str = ""
    rate_1: float = 0.0
    rate_2: float = 0.0
    rate_3: float = 0.0
    zus_costs: float = 0.0
    accounting_costs: float = 0.0
    initial_balance: float = 0.0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class MonthlyHours:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str = ""
    year: int = 0
    month: int = 0
    rate_1_hours: float | None = None
    rate_2_hours: float | None = None
    rate_3_hours: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class AdditionalEarning:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str = ""
    year: int = 0
    month: int = 0
    name: str = ""
    amount: float = 0.0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class ExpenseCategory:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str = ""
    name: str = ""
    color: str = "#6366f1"
    is_preset: bool = False
    sort_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Expense:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str = ""
    year: int = 0
    month: int = 0  # 0 = recurring, 1-12 = specific month
    name: str = ""
    amount: float = 0.0
    recurring: bool = False
    category_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class CarryForwardOverride:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    calendar_id: str = ""
    year: int = 0
    amount: float = 0.0
    created_at: datetime | None = None
    updated_at: datetime | None = None
