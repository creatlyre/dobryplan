from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from dateutil.rrule import rrulestr

from app.database.models import Event


@dataclass
class EventOccurrence:
    id: str
    calendar_id: str
    created_by_user_id: str | None
    title: str
    description: str | None
    start_at: datetime
    end_at: datetime
    timezone: str
    is_deleted: bool = False
    rrule: str | None = None


def validate_rrule(rrule_value: str, dtstart: datetime) -> None:
    try:
        rrulestr(rrule_value, dtstart=dtstart)
    except Exception as exc:
        raise ValueError(f"Invalid rrule: {exc}") from exc


def expand_event(event: Event, range_start: datetime, range_end: datetime) -> Iterable[EventOccurrence]:
    if not event.rrule:
        if range_start <= event.start_at <= range_end:
            yield EventOccurrence(
                id=event.id,
                calendar_id=event.calendar_id,
                created_by_user_id=event.created_by_user_id,
                title=event.title,
                description=event.description,
                start_at=event.start_at,
                end_at=event.end_at,
                timezone=event.timezone,
                rrule=event.rrule,
            )
        return

    duration = event.end_at - event.start_at
    rule = rrulestr(event.rrule, dtstart=event.start_at)
    for index, occurrence_start in enumerate(rule.between(range_start, range_end, inc=True)):
        occurrence_id = f"{event.id}:{index}:{occurrence_start.isoformat()}"
        yield EventOccurrence(
            id=occurrence_id,
            calendar_id=event.calendar_id,
            created_by_user_id=event.created_by_user_id,
            title=event.title,
            description=event.description,
            start_at=occurrence_start,
            end_at=occurrence_start + duration,
            timezone=event.timezone,
            rrule=event.rrule,
        )
