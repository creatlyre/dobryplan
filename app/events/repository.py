from datetime import datetime

from sqlalchemy import and_, extract
from sqlalchemy.orm import Session

from app.database.models import Event
from app.events.schemas import EventCreate, EventUpdate


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, calendar_id: str, user_id: str, payload: EventCreate) -> Event:
        event = Event(
            calendar_id=calendar_id,
            created_by_user_id=user_id,
            last_edited_by_user_id=user_id,
            title=payload.title,
            description=payload.description,
            start_at=payload.start_at,
            end_at=payload.end_at,
            timezone=payload.timezone,
            rrule=payload.rrule,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_by_id(self, event_id: str, calendar_id: str) -> Event | None:
        return (
            self.db.query(Event)
            .filter(
                and_(
                    Event.id == event_id,
                    Event.calendar_id == calendar_id,
                    Event.is_deleted.is_(False),
                )
            )
            .first()
        )

    def update(self, event: Event, user_id: str, payload: EventUpdate) -> Event:
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(event, key, value)
        event.last_edited_by_user_id = user_id
        event.updated_at = datetime.utcnow()
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def soft_delete(self, event: Event, user_id: str) -> Event:
        event.is_deleted = True
        event.last_edited_by_user_id = user_id
        event.updated_at = datetime.utcnow()
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_for_day(self, calendar_id: str, year: int, month: int, day: int) -> list[Event]:
        return (
            self.db.query(Event)
            .filter(
                and_(
                    Event.calendar_id == calendar_id,
                    Event.is_deleted.is_(False),
                    Event.rrule.is_(None),
                    extract("year", Event.start_at) == year,
                    extract("month", Event.start_at) == month,
                    extract("day", Event.start_at) == day,
                )
            )
            .order_by(Event.start_at.asc())
            .all()
        )

    def list_for_month(self, calendar_id: str, year: int, month: int) -> list[Event]:
        return (
            self.db.query(Event)
            .filter(
                and_(
                    Event.calendar_id == calendar_id,
                    Event.is_deleted.is_(False),
                    Event.rrule.is_(None),
                    extract("year", Event.start_at) == year,
                    extract("month", Event.start_at) == month,
                )
            )
            .order_by(Event.start_at.asc())
            .all()
        )

    def list_recurrence_roots_until(self, calendar_id: str, range_end: datetime) -> list[Event]:
        return (
            self.db.query(Event)
            .filter(
                and_(
                    Event.calendar_id == calendar_id,
                    Event.is_deleted.is_(False),
                    Event.rrule.is_not(None),
                    Event.start_at <= range_end,
                )
            )
            .order_by(Event.start_at.asc())
            .all()
        )
