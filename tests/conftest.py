import uuid
from datetime import datetime, timedelta
from dataclasses import asdict
from dataclasses import is_dataclass
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.database.database import Base, get_db
from app.database.models import Calendar, User
from config import Settings
import os

os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DB_ENCRYPTION_KEY"] = "test-encryption-key"

from main import app


class InMemoryStore:
    def __init__(self):
        self.tables: dict[str, list[dict[str, Any]]] = {
            "users": [],
            "calendars": [],
            "calendar_invitations": [],
            "events": [],
            "budget_settings": [],
            "monthly_hours": [],
            "additional_earnings": [],
            "expenses": [],
            "carry_forward_overrides": [],
        }

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    @staticmethod
    def _parse_filter(raw: str) -> tuple[str, str]:
        if "." not in raw:
            return "eq", raw
        op, value = raw.split(".", 1)
        return op, value

    @staticmethod
    def _coerce_for_compare(source: Any, target: Any) -> Any:
        if isinstance(source, bool):
            if isinstance(target, str):
                return target.lower() == "true"
            return bool(target)
        if isinstance(source, int) and isinstance(target, str):
            try:
                return int(target)
            except ValueError:
                return target
        if isinstance(source, float) and isinstance(target, str):
            try:
                return float(target)
            except ValueError:
                return target
        return target

    @classmethod
    def _matches(cls, row: dict[str, Any], key: str, raw_filter: str) -> bool:
        op, value = cls._parse_filter(raw_filter)
        current = row.get(key)
        target = cls._coerce_for_compare(current, value)

        if op == "eq":
            return current == target
        if op == "neq":
            return current != target
        if op == "lte":
            return current is not None and current <= target
        if op == "gte":
            return current is not None and current >= target
        return False

    def _apply_filters(
        self, rows: list[dict[str, Any]], params: dict[str, str] | None
    ) -> list[dict[str, Any]]:
        if not params:
            return list(rows)

        filtered = list(rows)
        for key, raw in params.items():
            if key in {"select", "limit", "order"}:
                continue
            filtered = [row for row in filtered if self._matches(row, key, raw)]

        order_spec = params.get("order")
        if order_spec:
            field, _, direction = order_spec.partition(".")
            reverse = direction.lower() == "desc"
            filtered.sort(key=lambda row: row.get(field) or "", reverse=reverse)

        limit = params.get("limit")
        if limit is not None:
            filtered = filtered[: int(limit)]

        return filtered

    def select(
        self, table: str, params: dict[str, str], auth_token: str | None = None
    ) -> list[dict[str, Any]]:
        rows = self._apply_filters(self.tables.get(table, []), params)
        return [dict(item) for item in rows]

    def insert(
        self, table: str, payload: dict[str, Any], auth_token: str | None = None
    ) -> dict[str, Any]:
        row = {key: self._normalize_value(value) for key, value in payload.items()}
        if not row.get("id"):
            row["id"] = str(uuid.uuid4())
        self.tables.setdefault(table, []).append(row)
        return dict(row)

    def update(
        self,
        table: str,
        filters: dict[str, str],
        payload: dict[str, Any],
        auth_token: str | None = None,
    ) -> dict[str, Any] | None:
        rows = self.tables.get(table, [])
        matched = [
            row
            for row in rows
            if all(self._matches(row, key, raw) for key, raw in filters.items())
        ]
        if not matched:
            return None

        normalized_payload = {
            key: self._normalize_value(value) for key, value in payload.items()
        }
        for row in matched:
            row.update(normalized_payload)
        return dict(matched[0])

    def count(
        self, table: str, filters: dict[str, str], auth_token: str | None = None
    ) -> int:
        return len(self._apply_filters(self.tables.get(table, []), filters))

    def delete(
        self, table: str, filters: dict[str, str], auth_token: str | None = None
    ) -> int:
        rows = self.tables.get(table, [])
        original_len = len(rows)
        self.tables[table] = [
            r
            for r in rows
            if not all(self._matches(r, k, v) for k, v in filters.items())
        ]
        return original_len - len(self.tables[table])

    def add(self, item: Any) -> None:
        if not is_dataclass(item):
            raise TypeError("Only dataclass models are supported in test store")

        if item.__class__.__name__ == "User":
            table = "users"
        elif item.__class__.__name__ == "Calendar":
            table = "calendars"
        elif item.__class__.__name__ == "CalendarInvitation":
            table = "calendar_invitations"
        elif item.__class__.__name__ == "Event":
            table = "events"
        elif item.__class__.__name__ == "BudgetSettings":
            table = "budget_settings"
        elif item.__class__.__name__ == "MonthlyHours":
            table = "monthly_hours"
        elif item.__class__.__name__ == "AdditionalEarning":
            table = "additional_earnings"
        elif item.__class__.__name__ == "CarryForwardOverride":
            table = "carry_forward_overrides"
        else:
            raise ValueError(f"Unsupported model for add(): {item.__class__.__name__}")

        payload = asdict(item)
        self.insert(table, payload)

    def commit(self) -> None:
        return None

    def refresh(self, _item: Any) -> None:
        if not is_dataclass(_item):
            return None

        if _item.__class__.__name__ == "User":
            table = "users"
        elif _item.__class__.__name__ == "Calendar":
            table = "calendars"
        elif _item.__class__.__name__ == "CalendarInvitation":
            table = "calendar_invitations"
        elif _item.__class__.__name__ == "Event":
            table = "events"
        elif _item.__class__.__name__ == "BudgetSettings":
            table = "budget_settings"
        elif _item.__class__.__name__ == "MonthlyHours":
            table = "monthly_hours"
        elif _item.__class__.__name__ == "AdditionalEarning":
            table = "additional_earnings"
        elif _item.__class__.__name__ == "CarryForwardOverride":
            table = "carry_forward_overrides"
        else:
            return None

        item_id = getattr(_item, "id", None)
        if not item_id:
            return None

        rows = self.select(table, {"id": f"eq.{item_id}", "limit": "1"})
        if not rows:
            return None

        row = rows[0]
        for key in row.keys():
            if hasattr(_item, key):
                setattr(_item, key, row[key])
        return None


@pytest.fixture
def test_db():
    _ = Base
    yield InMemoryStore()


@pytest.fixture
def test_client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_a(test_db):
    calendar = Calendar(
        id=str(uuid.uuid4()),
        name="Household A",
    )
    test_db.add(calendar)
    test_db.commit()

    user = User(
        id=str(uuid.uuid4()),
        email="usera@example.com",
        name="User A",
        google_id="google_a",
        calendar_id=calendar.id,
        last_login=datetime.utcnow(),
    )
    calendar.owner_user_id = user.id
    test_db.add(user)
    test_db.add(calendar)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_user_b(test_db):
    user = User(
        id=str(uuid.uuid4()),
        email="userb@example.com",
        name="User B",
        google_id="google_b",
        last_login=datetime.utcnow(),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def authenticated_client(test_db, test_user_a: User):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    async def override_get_current_user():
        return test_user_a

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)
    settings = Settings()
    token = jwt.encode(
        {
            "user_id": test_user_a.id,
            "email": test_user_a.email,
            "exp": datetime.utcnow() + timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    client.cookies.set("session", token, domain="testserver", path="/")
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def locale_reset_client(authenticated_client):
    """Test client with locale state cleared (cookie, localStorage sim)."""
    # Clear locale cookie before each test
    authenticated_client.cookies.delete("locale", domain=None, path=None)
    yield authenticated_client
    # Teardown: clear cookie again
    authenticated_client.cookies.delete("locale", domain=None, path=None)


def get_page_in_locale(client, path, locale="pl"):
    """Fetch page with locale query param or cookie."""
    if locale == "pl":
        # Use default, no param needed
        return client.get(path)
    else:
        # Request with locale param
        return client.get(f"{path}?lang={locale}")


def assert_locale_rendered(html_text, expected_locale):
    """Verify locale identifier in page (e.g., 'pl-PL', Polish label)."""
    if expected_locale == "pl":
        assert 'lang="pl"' in html_text or "Wyloguj" in html_text  # Polish logout
    elif expected_locale == "en":
        assert 'lang="en"' in html_text or "Logout" in html_text  # English logout


def assert_contains_any(text, *candidates):
    """Check if text contains any of the candidate strings."""
    for candidate in candidates:
        if candidate in text:
            return True
    raise AssertionError(f"None of {candidates} found in text")
