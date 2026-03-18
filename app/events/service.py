from datetime import datetime
from datetime import timedelta

from app.events.recurrence import expand_event, validate_rrule
from app.events.repository import EventRepository
from app.events.schemas import EventCreate, EventUpdate


class EventService:
    def __init__(self, repository: EventRepository):
        self.repository = repository

    @staticmethod
    def _validate_range(start_at: datetime, end_at: datetime) -> None:
        if start_at >= end_at:
            raise ValueError("start_at must be before end_at")

    def create_event(self, calendar_id: str, user_id: str, payload: EventCreate):
        self._validate_range(payload.start_at, payload.end_at)
        if payload.rrule:
            validate_rrule(payload.rrule, payload.start_at)
        return self.repository.create(calendar_id, user_id, payload)

    def update_event(self, event_id: str, calendar_id: str, user_id: str, payload: EventUpdate):
        event = self.repository.get_by_id(event_id, calendar_id)
        if not event:
            raise ValueError("Event not found")

        next_start = payload.start_at or event.start_at
        next_end = payload.end_at or event.end_at
        self._validate_range(next_start, next_end)
        if payload.rrule:
            validate_rrule(payload.rrule, next_start)

        return self.repository.update(event, user_id, payload)

    def delete_event(self, event_id: str, calendar_id: str, user_id: str):
        event = self.repository.get_by_id(event_id, calendar_id)
        if not event:
            raise ValueError("Event not found")
        return self.repository.soft_delete(event, user_id)

    def list_day(self, calendar_id: str, year: int, month: int, day: int):
        return self.repository.list_for_day(calendar_id, year, month, day)

    def list_month(self, calendar_id: str, year: int, month: int):
        return self.repository.list_for_month(calendar_id, year, month)

    def list_day_expanded(self, calendar_id: str, year: int, month: int, day: int):
        range_start = datetime(year, month, day, 0, 0, 0)
        range_end = datetime(year, month, day, 23, 59, 59)

        base_events = self.repository.list_for_day(calendar_id, year, month, day)
        recurrence_roots = self.repository.list_recurrence_roots_until(calendar_id, range_end)

        expanded = list(base_events)
        for root in recurrence_roots:
            expanded.extend(expand_event(root, range_start, range_end))

        return sorted(expanded, key=lambda item: item.start_at)

    def list_month_expanded(self, calendar_id: str, year: int, month: int):
        range_start = datetime(year, month, 1, 0, 0, 0)
        if month == 12:
            next_month = datetime(year + 1, 1, 1, 0, 0, 0)
        else:
            next_month = datetime(year, month + 1, 1, 0, 0, 0)
        range_end = next_month - timedelta(seconds=1)

        base_events = self.repository.list_for_month(calendar_id, year, month)
        recurrence_roots = self.repository.list_recurrence_roots_until(calendar_id, range_end)

        expanded = list(base_events)
        for root in recurrence_roots:
            expanded.extend(expand_event(root, range_start, range_end))

        return sorted(expanded, key=lambda item: item.start_at)
