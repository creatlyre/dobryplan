from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.auth.oauth import refresh_access_token
from app.auth.utils import decrypt_token, encrypt_token
from app.database.models import Event, User
from app.users.repository import UserRepository
from app.events.repository import EventRepository
from app.events.schemas import EventUpdate
from app.events.service import EventService
from config import Settings


@dataclass
class SyncResult:
    users_synced: int
    events_synced: int
    errors: list[str]


@dataclass
class ImportResult:
    events_imported: int
    events_updated: int
    calendars_scanned: int
    errors: list[str]


class GoogleSyncService:
    def __init__(self, db):
        self.db = db
        self.settings = Settings()
        self.user_repo = UserRepository(db)

    def _household_users(self, calendar_id: str) -> list[User]:
        rows = self.db.select("users", {"calendar_id": f"eq.{calendar_id}"})
        users = [self.user_repo.get_user_by_id(item.get("id")) for item in rows if item.get("id")]
        return [user for user in users if user is not None]

    def _credentials_for_user(self, user: User) -> Credentials | None:
        if not user.google_refresh_token and not user.google_access_token:
            return None

        token = decrypt_token(user.google_access_token) if user.google_access_token else None
        refresh_token = decrypt_token(user.google_refresh_token) if user.google_refresh_token else None

        creds = Credentials(
            token=token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.settings.GOOGLE_CLIENT_ID,
            client_secret=self.settings.GOOGLE_CLIENT_SECRET,
            scopes=self.settings.GOOGLE_SCOPES,
        )

        if user.google_token_expiry and user.google_token_expiry <= datetime.utcnow() and refresh_token:
            refreshed = refresh_access_token(refresh_token)
            if not refreshed:
                return None
            user.google_access_token = encrypt_token(refreshed["access_token"])
            if refreshed.get("refresh_token"):
                user.google_refresh_token = encrypt_token(refreshed["refresh_token"])
            user.google_token_expiry = refreshed.get("token_expiry")
            self.user_repo.update_user(
                user.id,
                {
                    "google_access_token": user.google_access_token,
                    "google_refresh_token": user.google_refresh_token,
                    "google_token_expiry": user.google_token_expiry.isoformat() if user.google_token_expiry else None,
                },
            )

            creds = Credentials(
                token=refreshed["access_token"],
                refresh_token=decrypt_token(user.google_refresh_token) if user.google_refresh_token else None,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.settings.GOOGLE_CLIENT_ID,
                client_secret=self.settings.GOOGLE_CLIENT_SECRET,
                scopes=self.settings.GOOGLE_SCOPES,
            )

        return creds

    @staticmethod
    def _sync_calendar_name(user: User) -> str:
        suffix = user.email.split("@")[0] if user.email else user.id[:8]
        return f"CalendarPlanner Sync ({suffix})"

    def _google_service(self, creds: Credentials):
        return build("calendar", "v3", credentials=creds, cache_discovery=False)

    def _ensure_user_calendar(self, service, user: User) -> str:
        target_name = self._sync_calendar_name(user)
        calendars = service.calendarList().list().execute().get("items", [])

        for cal in calendars:
            if cal.get("summary") == target_name:
                return cal["id"]

        created = service.calendars().insert(body={"summary": target_name, "timeZone": "UTC"}).execute()
        return created["id"]

    def _import_calendar_ids(self, service, user: User) -> list[str]:
        ids: list[str] = ["primary"]
        target_name = self._sync_calendar_name(user)
        try:
            calendars = service.calendarList().list().execute().get("items", [])
            for cal in calendars:
                cal_id = cal.get("id")
                if not cal_id:
                    continue
                if cal_id not in ids and cal.get("summary") == target_name:
                    ids.append(cal_id)
        except Exception:
            return ids
        return ids

    def _event_body(self, event: Event) -> dict:
        reminder_minutes = getattr(event, "reminder_minutes", None)
        if reminder_minutes is None:
            reminder_minutes = self.settings.GOOGLE_EVENT_REMINDER_MINUTES

        reminders: dict[str, object]
        try:
            minutes_int = int(reminder_minutes)
        except (TypeError, ValueError):
            minutes_int = -1

        if minutes_int > 0:
            reminders = {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": minutes_int}
                ],
            }
        else:
            reminders = {"useDefault": True}

        return {
            "summary": event.title,
            "description": event.description or "",
            "start": {"dateTime": event.start_at.isoformat(), "timeZone": event.timezone or "UTC"},
            "end": {"dateTime": event.end_at.isoformat(), "timeZone": event.timezone or "UTC"},
            "recurrence": [f"RRULE:{event.rrule}"] if event.rrule else [],
            "reminders": reminders,
            "extendedProperties": {
                "private": {
                    "cp_event_id": event.id,
                    "cp_visibility": getattr(event, "visibility", "shared") or "shared",
                    "cp_owner_id": event.created_by_user_id,
                }
            },
        }

    @staticmethod
    def _month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
        start = datetime(year, month, 1, 0, 0, 0)
        if month == 12:
            next_month = datetime(year + 1, 1, 1, 0, 0, 0)
        else:
            next_month = datetime(year, month + 1, 1, 0, 0, 0)
        return start, next_month

    @staticmethod
    def _parse_google_dt(raw: dict | None) -> datetime | None:
        if not raw:
            return None

        iso = raw.get("dateTime")
        if iso:
            if iso.endswith("Z"):
                iso = iso.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(iso)
                if parsed.tzinfo is not None:
                    return parsed.astimezone(timezone.utc).replace(tzinfo=None)
                return parsed
            except ValueError:
                return None

        date_only = raw.get("date")
        if date_only:
            try:
                return datetime.fromisoformat(date_only)
            except ValueError:
                return None

        return None

    @staticmethod
    def _extract_cp_event_id(google_event: dict) -> str | None:
        ext = google_event.get("extendedProperties") or {}
        private = ext.get("private") or {}
        cp_event_id = private.get("cp_event_id")
        if isinstance(cp_event_id, str) and cp_event_id.strip():
            return cp_event_id.strip()
        return None

    @staticmethod
    def _extract_cp_visibility(google_event: dict) -> str:
        ext = google_event.get("extendedProperties") or {}
        private = ext.get("private") or {}
        vis = private.get("cp_visibility")
        if vis in ("shared", "private"):
            return vis
        return "shared"

    def _find_local_event_by_google_id(self, calendar_id: str, google_event_id: str) -> Event | None:
        rows = self.db.select(
            "events",
            {
                "calendar_id": f"eq.{calendar_id}",
                "google_event_id": f"eq.{google_event_id}",
                "is_deleted": "eq.false",
                "limit": "1",
            },
        )
        if not rows:
            return None
        return EventRepository(self.db).get_by_id(rows[0].get("id"), calendar_id)

    def _upsert_google_event(self, calendar_id: str, user_id: str, google_event: dict) -> tuple[int, int]:
        google_event_id = google_event.get("id")
        if not google_event_id:
            return 0, 0

        if google_event.get("status") == "cancelled":
            cp_event_id = self._extract_cp_event_id(google_event)
            target = EventRepository(self.db).get_by_id(cp_event_id, calendar_id) if cp_event_id else None
            if not target:
                target = self._find_local_event_by_google_id(calendar_id, google_event_id)
            if target:
                EventRepository(self.db).soft_delete(target, user_id)
                return 0, 1
            return 0, 0

        start_at = self._parse_google_dt(google_event.get("start"))
        end_at = self._parse_google_dt(google_event.get("end"))
        if not start_at:
            return 0, 0
        if not end_at or end_at <= start_at:
            end_at = start_at + timedelta(hours=1)

        timezone = (
            (google_event.get("start") or {}).get("timeZone")
            or (google_event.get("end") or {}).get("timeZone")
            or "UTC"
        )
        recurrence = google_event.get("recurrence") or []
        rrule = None
        if recurrence:
            for rule in recurrence:
                if isinstance(rule, str) and rule.startswith("RRULE:"):
                    rrule = rule[len("RRULE:") :]
                    break

        event_title = google_event.get("summary") or "Untitled"
        event_description = google_event.get("description")

        cp_event_id = self._extract_cp_event_id(google_event)
        existing = EventRepository(self.db).get_by_id(cp_event_id, calendar_id) if cp_event_id else None
        if not existing:
            existing = self._find_local_event_by_google_id(calendar_id, google_event_id)

        if existing:
            updated = EventRepository(self.db).update(
                existing,
                user_id,
                EventUpdate(
                    title=event_title,
                    description=event_description,
                    start_at=start_at,
                    end_at=end_at,
                    timezone=timezone,
                    rrule=rrule,
                ),
            )
            self.db.update(
                "events",
                {"id": f"eq.{updated.id}"},
                {
                    "google_event_id": google_event_id,
                    "google_sync_at": datetime.utcnow().isoformat(),
                },
            )
            return 0, 1

        inserted = self.db.insert(
            "events",
            {
                "id": cp_event_id or str(uuid.uuid4()),
                "calendar_id": calendar_id,
                "created_by_user_id": user_id,
                "last_edited_by_user_id": user_id,
                "title": event_title,
                "description": event_description,
                "start_at": start_at.isoformat(),
                "end_at": end_at.isoformat(),
                "timezone": timezone,
                "rrule": rrule,
                "visibility": self._extract_cp_visibility(google_event),
                "google_event_id": google_event_id,
                "google_sync_at": datetime.utcnow().isoformat(),
                "is_deleted": False,
            },
        )
        return (1, 0) if inserted else (0, 0)

    def _find_google_event(self, service, calendar_id: str, app_event_id: str):
        items = (
            service.events()
            .list(calendarId=calendar_id, privateExtendedProperty=f"cp_event_id={app_event_id}", showDeleted=True)
            .execute()
            .get("items", [])
        )
        return items[0] if items else None

    def _sync_recipients(self, event: Event) -> list[User]:
        """Return the list of users who should receive this event via Google sync.

        Shared events go to all household users. Private events go only to the owner.
        """
        users = self._household_users(event.calendar_id)
        visibility = getattr(event, "visibility", "shared") or "shared"
        if visibility == "private":
            return [u for u in users if u.id == event.created_by_user_id]
        return users

    def sync_event_for_household(self, event: Event, deleted: bool = False) -> SyncResult:
        users = self._sync_recipients(event)
        synced_users = 0
        synced_events = 0
        errors: list[str] = []

        for user in users:
            try:
                creds = self._credentials_for_user(user)
                if not creds:
                    continue

                service = self._google_service(creds)
                calendar_id = self._ensure_user_calendar(service, user)
                existing = self._find_google_event(service, calendar_id, event.id)

                if deleted:
                    if existing:
                        service.events().delete(calendarId=calendar_id, eventId=existing["id"]).execute()
                        synced_events += 1
                else:
                    payload = self._event_body(event)
                    if existing:
                        service.events().update(calendarId=calendar_id, eventId=existing["id"], body=payload).execute()
                    else:
                        service.events().insert(calendarId=calendar_id, body=payload).execute()
                    synced_events += 1

                synced_users += 1
            except Exception as exc:
                errors.append(f"{user.email}: {exc}")

        if hasattr(event, "google_sync_at"):
            event.google_sync_at = datetime.utcnow()
            self.db.update(
                "events",
                {"id": f"eq.{event.id}"},
                {"google_sync_at": event.google_sync_at.isoformat()},
            )
        return SyncResult(users_synced=synced_users, events_synced=synced_events, errors=errors)

    def export_month(self, user: User, year: int, month: int) -> SyncResult:
        service = EventService(EventRepository(self.db))
        events = service.list_month_expanded(user.calendar_id, year, month)

        total_users = 0
        total_events = 0
        errors: list[str] = []
        for item in events:
            if not hasattr(item, "calendar_id"):
                continue
            result = self.sync_event_for_household(item, deleted=False)
            total_users += result.users_synced
            total_events += result.events_synced
            errors.extend(result.errors)

        if user.calendar_id and not errors:
            self.db.update(
                "calendars",
                {"id": f"eq.{user.calendar_id}"},
                {"last_sync_at": datetime.utcnow().isoformat()},
            )

        return SyncResult(users_synced=total_users, events_synced=total_events, errors=errors)

    def import_month(self, user: User, year: int, month: int) -> ImportResult:
        errors: list[str] = []
        imported = 0
        updated = 0

        if not user.calendar_id:
            return ImportResult(events_imported=0, events_updated=0, calendars_scanned=0, errors=["User has no calendar_id"])

        creds = self._credentials_for_user(user)
        if not creds:
            return ImportResult(events_imported=0, events_updated=0, calendars_scanned=0, errors=["Google account is not connected"])

        try:
            service = self._google_service(creds)
            google_calendar_ids = self._import_calendar_ids(service, user)
            start, next_month = self._month_bounds(year, month)

            for google_calendar_id in google_calendar_ids:
                page_token = None
                while True:
                    response = (
                        service.events()
                        .list(
                            calendarId=google_calendar_id,
                            timeMin=start.isoformat() + "Z",
                            timeMax=next_month.isoformat() + "Z",
                            singleEvents=True,
                            showDeleted=True,
                            maxResults=250,
                            pageToken=page_token,
                        )
                        .execute()
                    )
                    items = response.get("items", [])
                    for item in items:
                        try:
                            add_count, update_count = self._upsert_google_event(user.calendar_id, user.id, item)
                            imported += add_count
                            updated += update_count
                        except Exception as exc:
                            errors.append(f"{item.get('id', 'unknown')}: {exc}")

                    page_token = response.get("nextPageToken")
                    if not page_token:
                        break

            if not errors:
                self.db.update(
                    "calendars",
                    {"id": f"eq.{user.calendar_id}"},
                    {"last_sync_at": datetime.utcnow().isoformat()},
                )
        except Exception as exc:
            errors.append(str(exc))

        return ImportResult(
            events_imported=imported,
            events_updated=updated,
            calendars_scanned=len(google_calendar_ids) if 'google_calendar_ids' in locals() else 0,
            errors=errors,
        )
