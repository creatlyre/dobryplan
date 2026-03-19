import uuid
from datetime import datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import User
from app.events.ocr import OCRParseResult
from config import Settings
from main import app


def _payload(title: str, start: datetime, end: datetime, visibility: str = "shared") -> dict:
    return {
        "title": title,
        "description": "desc",
        "start_at": start.isoformat(),
        "end_at": end.isoformat(),
        "timezone": "UTC",
        "visibility": visibility,
    }


def test_create_event(authenticated_client):
    now = datetime.utcnow().replace(microsecond=0)
    response = authenticated_client.post(
        "/api/events",
        json=_payload("Doctor", now + timedelta(hours=1), now + timedelta(hours=2)),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"]
    assert data["title"] == "Doctor"


def test_update_event(authenticated_client):
    now = datetime.utcnow().replace(microsecond=0)
    create_response = authenticated_client.post(
        "/api/events",
        json=_payload("Initial", now + timedelta(hours=1), now + timedelta(hours=2)),
    )
    event_id = create_response.json()["id"]

    update_response = authenticated_client.put(
        f"/api/events/{event_id}",
        json={"title": "Updated Title"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated Title"


def test_delete_event_hides_from_month(authenticated_client):
    now = datetime.utcnow().replace(microsecond=0)
    create_response = authenticated_client.post(
        "/api/events",
        json=_payload("Temporary", now + timedelta(hours=1), now + timedelta(hours=2)),
    )
    event_id = create_response.json()["id"]

    delete_response = authenticated_client.delete(f"/api/events/{event_id}")
    assert delete_response.status_code == 200

    month_response = authenticated_client.get(f"/api/events/month?year={now.year}&month={now.month}")
    assert month_response.status_code == 200
    ids = [item["id"] for item in month_response.json()]
    assert event_id not in ids


def test_parse_event_natural_language(authenticated_client):
    """Test parsing natural language event text."""
    response = authenticated_client.post(
        "/api/events/parse",
        json={
            "text": "dentist tomorrow 2pm",
            "context_date": "2026-03-19",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "dentist" in data["title"].lower()
    assert data["start_at"] is not None
    assert data["timezone"] is not None
    assert isinstance(data["confidence_date"], float)
    assert isinstance(data["confidence_title"], float)
    assert isinstance(data["errors"], list)


def test_parse_event_with_errors(authenticated_client):
    """Test parsing that results in errors."""
    response = authenticated_client.post(
        "/api/events/parse",
        json={
            "text": "meeting at 2pm",  # No date, only time
            "context_date": "2026-03-19",
        },
    )

    assert response.status_code == 200
    data = response.json()
    # Should either have errors or low confidence
    assert isinstance(data["errors"], list)


def test_parse_event_uses_calendar_timezone(authenticated_client, test_db, test_user_a):
    """Regression: parse endpoint should propagate user calendar timezone, not hardcoded UTC."""
    test_db.update(
        "calendars",
        {"id": f"eq.{test_user_a.calendar_id}"},
        {"timezone": "America/New_York"},
    )

    response = authenticated_client.post(
        "/api/events/parse",
        json={
            "text": "dentist tomorrow 2pm",
            "context_date": "2026-03-19",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["timezone"] == "America/New_York"


def test_ocr_parse_event_success(authenticated_client, monkeypatch):
    now = datetime(2026, 3, 20, 14, 0, 0)

    def fake_parse_image(self, image_bytes, timezone, context_date, locale="en"):
        assert image_bytes == b"fake-image-bytes"
        return OCRParseResult(
            title="School concert",
            start_at=now,
            end_at=now + timedelta(hours=1),
            timezone=timezone,
            confidence_title=0.82,
            confidence_date=0.79,
            confidence_raw=0.88,
            raw_text="School concert Friday 2pm",
            errors=[],
        )

    monkeypatch.setattr("app.events.routes.OCRService.parse_image", fake_parse_image)

    response = authenticated_client.post(
        "/api/events/ocr-parse",
        data={"context_date": "2026-03-19"},
        files={"image": ("flyer.png", b"fake-image-bytes", "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "School concert"
    assert data["raw_text"] == "School concert Friday 2pm"
    assert data["confidence_raw"] == 0.88
    assert data["errors"] == []


def test_ocr_parse_event_empty_upload(authenticated_client):
    response = authenticated_client.post(
        "/api/events/ocr-parse",
        data={"context_date": "2026-03-19"},
        files={"image": ("empty.png", b"", "image/png")},
    )

    assert response.status_code == 400


# ── Visibility tests ─────────────────────────────────────────────────────────


def test_create_event_defaults_visibility_to_shared(authenticated_client):
    """Omitting visibility field defaults to shared for backward compat."""
    now = datetime.utcnow().replace(microsecond=0)
    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Default vis",
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "UTC",
        },
    )
    assert response.status_code == 201
    assert response.json()["visibility"] == "shared"


def test_create_event_explicit_private(authenticated_client):
    now = datetime.utcnow().replace(microsecond=0)
    response = authenticated_client.post(
        "/api/events",
        json=_payload("Solo task", now + timedelta(hours=1), now + timedelta(hours=2), visibility="private"),
    )
    assert response.status_code == 201
    assert response.json()["visibility"] == "private"


def test_create_event_invalid_visibility_rejected(authenticated_client):
    now = datetime.utcnow().replace(microsecond=0)
    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Bad vis",
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "UTC",
            "visibility": "secret",
        },
    )
    assert response.status_code == 422


def test_update_event_visibility(authenticated_client):
    now = datetime.utcnow().replace(microsecond=0)
    create = authenticated_client.post(
        "/api/events",
        json=_payload("Toggleable", now + timedelta(hours=1), now + timedelta(hours=2)),
    )
    event_id = create.json()["id"]

    update = authenticated_client.put(
        f"/api/events/{event_id}",
        json={"visibility": "private"},
    )
    assert update.status_code == 200
    assert update.json()["visibility"] == "private"


@pytest.fixture
def _household_user_b(test_db, test_user_a):
    """Second user in the same household calendar as test_user_a."""
    user_b = User(
        id=str(uuid.uuid4()),
        email="partnerb@example.com",
        name="Partner B",
        google_id="google_b_household",
        calendar_id=test_user_a.calendar_id,
        last_login=datetime.utcnow(),
    )
    test_db.add(user_b)
    test_db.commit()
    test_db.refresh(user_b)
    return user_b


def _make_client_for_user(test_db, user):
    """Create an authenticated TestClient bound to a specific user."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    async def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)
    settings = Settings()
    token = jwt.encode(
        {
            "user_id": user.id,
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    client.cookies.set("session", token, domain="testserver", path="/")
    return client


def test_private_event_hidden_from_other_user_month(test_db, test_user_a, _household_user_b):
    """Private events by user A should not appear in user B month listing."""
    now = datetime.utcnow().replace(microsecond=0)

    # Create private event as user A
    client_a = _make_client_for_user(test_db, test_user_a)
    create = client_a.post(
        "/api/events",
        json=_payload("A secret", now + timedelta(hours=1), now + timedelta(hours=2), visibility="private"),
    )
    assert create.status_code == 201
    event_id = create.json()["id"]

    # User A should see it
    month_a = client_a.get(f"/api/events/month?year={now.year}&month={now.month}")
    ids_a = [e["id"] for e in month_a.json()]
    assert event_id in ids_a

    # Switch to user B — should NOT see it
    client_b = _make_client_for_user(test_db, _household_user_b)
    month_b = client_b.get(f"/api/events/month?year={now.year}&month={now.month}")
    ids_b = [e["id"] for e in month_b.json()]
    assert event_id not in ids_b

    app.dependency_overrides.clear()


def test_private_event_hidden_from_other_user_day(test_db, test_user_a, _household_user_b):
    """Private events by user A should not appear in user B day listing."""
    now = datetime.utcnow().replace(microsecond=0)

    client_a = _make_client_for_user(test_db, test_user_a)
    create = client_a.post(
        "/api/events",
        json=_payload("A day secret", now + timedelta(hours=1), now + timedelta(hours=2), visibility="private"),
    )
    assert create.status_code == 201
    event_id = create.json()["id"]

    client_b = _make_client_for_user(test_db, _household_user_b)
    day_b = client_b.get(f"/api/events/day?year={now.year}&month={now.month}&day={now.day}")
    ids_b = [e["id"] for e in day_b.json()]
    assert event_id not in ids_b

    app.dependency_overrides.clear()


def test_shared_event_visible_to_both_users(test_db, test_user_a, _household_user_b):
    """Shared events remain visible to both household members."""
    now = datetime.utcnow().replace(microsecond=0)

    client_a = _make_client_for_user(test_db, test_user_a)
    create = client_a.post(
        "/api/events",
        json=_payload("Family dinner", now + timedelta(hours=1), now + timedelta(hours=2), visibility="shared"),
    )
    event_id = create.json()["id"]

    client_b = _make_client_for_user(test_db, _household_user_b)
    month_b = client_b.get(f"/api/events/month?year={now.year}&month={now.month}")
    ids_b = [e["id"] for e in month_b.json()]
    assert event_id in ids_b

    app.dependency_overrides.clear()


def test_other_user_cannot_update_private_event(test_db, test_user_a, _household_user_b):
    """User B should get 404 trying to update user A's private event."""
    now = datetime.utcnow().replace(microsecond=0)

    client_a = _make_client_for_user(test_db, test_user_a)
    create = client_a.post(
        "/api/events",
        json=_payload("A private", now + timedelta(hours=1), now + timedelta(hours=2), visibility="private"),
    )
    event_id = create.json()["id"]

    client_b = _make_client_for_user(test_db, _household_user_b)
    update = client_b.put(f"/api/events/{event_id}", json={"title": "Hijacked"})
    assert update.status_code == 404

    app.dependency_overrides.clear()


def test_other_user_cannot_delete_private_event(test_db, test_user_a, _household_user_b):
    """User B should get 404 trying to delete user A's private event."""
    now = datetime.utcnow().replace(microsecond=0)

    client_a = _make_client_for_user(test_db, test_user_a)
    create = client_a.post(
        "/api/events",
        json=_payload("A private del", now + timedelta(hours=1), now + timedelta(hours=2), visibility="private"),
    )
    event_id = create.json()["id"]

    client_b = _make_client_for_user(test_db, _household_user_b)
    delete = client_b.delete(f"/api/events/{event_id}")
    assert delete.status_code == 404

    app.dependency_overrides.clear()
