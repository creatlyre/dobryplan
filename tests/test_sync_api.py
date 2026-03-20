from datetime import datetime
from types import SimpleNamespace

from app.database.models import Event
from app.sync.service import GoogleSyncService


def test_sync_status(authenticated_client):
    response = authenticated_client.get("/api/sync/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"ready", "google_not_connected", "oauth_not_configured"}
    assert "google_connected" in data
    assert "oauth_configured" in data
    assert data["connect_url"] == "/auth/login"
    assert "last_successful_sync_at" in data


def test_export_month_uses_service(authenticated_client, monkeypatch):
    called = {"ok": False}

    class FakeResult:
        users_synced = 2
        events_synced = 3
        errors = []

    def fake_export_month(self, user, year, month):
        called["ok"] = True
        assert year == 2026
        assert month == 3
        return FakeResult()

    import app.sync.service

    monkeypatch.setattr(app.sync.service.GoogleSyncService, "export_month", fake_export_month)

    response = authenticated_client.post("/api/sync/export-month?year=2026&month=3")
    assert response.status_code == 200
    data = response.json()
    assert data["users_synced"] == 2
    assert data["events_synced"] == 3
    assert called["ok"]


def test_import_month_uses_service(authenticated_client, monkeypatch):
    called = {"ok": False}

    class FakeResult:
        events_imported = 4
        events_updated = 2
        calendars_scanned = 2
        errors = []

    def fake_import_month(self, user, year, month):
        called["ok"] = True
        assert year == 2026
        assert month == 3
        return FakeResult()

    import app.sync.service

    monkeypatch.setattr(app.sync.service.GoogleSyncService, "import_month", fake_import_month)

    response = authenticated_client.post("/api/sync/import-month?year=2026&month=3")
    assert response.status_code == 200
    data = response.json()
    assert data["events_imported"] == 4
    assert data["events_updated"] == 2
    assert data["calendars_scanned"] == 2
    assert data["requires_reauth"] is False
    assert called["ok"]


def test_import_month_sets_requires_reauth_on_scope_error(authenticated_client, monkeypatch):
    class FakeResult:
        events_imported = 0
        events_updated = 0
        calendars_scanned = 1
        errors = ["insufficientPermissions"]

    def fake_import_month(self, user, year, month):
        return FakeResult()

    import app.sync.service

    monkeypatch.setattr(app.sync.service.GoogleSyncService, "import_month", fake_import_month)

    response = authenticated_client.post("/api/sync/import-month?year=2026&month=3")
    assert response.status_code == 200
    assert response.json()["requires_reauth"] is True


def test_sync_status_returns_calendar_last_sync(authenticated_client, test_db, test_user_a):
    stamp = datetime(2026, 3, 19, 10, 30, 0).isoformat()
    test_db.update("calendars", {"id": f"eq.{test_user_a.calendar_id}"}, {"last_sync_at": stamp})

    response = authenticated_client.get("/api/sync/status")
    assert response.status_code == 200
    assert response.json()["last_successful_sync_at"] == stamp


def test_event_body_defaults_to_google_default_reminders(test_db):
    """Event with no reminder config → useDefault=True (Google handles default)."""
    service = GoogleSyncService(test_db)
    event = Event(
        id="evt-1",
        title="Reminder event",
        description="",
        start_at=datetime(2026, 3, 20, 9, 0, 0),
        end_at=datetime(2026, 3, 20, 10, 0, 0),
        timezone="UTC",
        created_by_user_id="user-1",
    )

    body = service._event_body(event)

    assert "reminders" in body
    assert body["reminders"]["useDefault"] is True


def test_event_body_single_reminder_backward_compat(test_db):
    """Event with only reminder_minutes → single popup override (backward compat)."""
    service = GoogleSyncService(test_db)
    event = Event(
        id="evt-2",
        title="Custom reminder",
        description="",
        start_at=datetime(2026, 3, 20, 11, 0, 0),
        end_at=datetime(2026, 3, 20, 12, 0, 0),
        timezone="UTC",
        reminder_minutes=5,
        created_by_user_id="user-2",
    )

    body = service._event_body(event)
    assert body["reminders"]["useDefault"] is False
    assert len(body["reminders"]["overrides"]) == 1
    assert body["reminders"]["overrides"][0] == {"method": "popup", "minutes": 5}


def test_event_body_multiple_reminders(test_db):
    """Event with reminder_minutes_list → multiple popup overrides."""
    service = GoogleSyncService(test_db)
    event = Event(
        id="evt-3",
        title="Multi reminder",
        description="",
        start_at=datetime(2026, 3, 20, 10, 0, 0),
        end_at=datetime(2026, 3, 20, 11, 0, 0),
        timezone="UTC",
        reminder_minutes_list=[30, 1440],
        created_by_user_id="user-3",
    )

    body = service._event_body(event)
    assert body["reminders"]["useDefault"] is False
    assert len(body["reminders"]["overrides"]) == 2
    assert body["reminders"]["overrides"][0] == {"method": "popup", "minutes": 30}
    assert body["reminders"]["overrides"][1] == {"method": "popup", "minutes": 1440}


def test_event_body_list_takes_precedence_over_single(test_db):
    """When both fields set, reminder_minutes_list wins."""
    service = GoogleSyncService(test_db)
    event = Event(
        id="evt-4",
        title="Precedence test",
        description="",
        start_at=datetime(2026, 3, 20, 14, 0, 0),
        end_at=datetime(2026, 3, 20, 15, 0, 0),
        timezone="UTC",
        reminder_minutes=10,
        reminder_minutes_list=[30, 60],
        created_by_user_id="user-4",
    )

    body = service._event_body(event)
    assert body["reminders"]["useDefault"] is False
    assert len(body["reminders"]["overrides"]) == 2
    assert body["reminders"]["overrides"][0]["minutes"] == 30
    assert body["reminders"]["overrides"][1]["minutes"] == 60


# ── Phase 8 visibility-aware sync ─────────────────────────────────────────


def test_event_body_includes_visibility_metadata(test_db):
    service = GoogleSyncService(test_db)
    event = Event(
        id="evt-vis-1",
        title="Private meeting",
        description="",
        start_at=datetime(2026, 3, 20, 9, 0, 0),
        end_at=datetime(2026, 3, 20, 10, 0, 0),
        timezone="UTC",
        visibility="private",
        created_by_user_id="owner-123",
    )
    body = service._event_body(event)
    ext_private = body["extendedProperties"]["private"]
    assert ext_private["cp_event_id"] == "evt-vis-1"
    assert ext_private["cp_visibility"] == "private"
    assert ext_private["cp_owner_id"] == "owner-123"


def test_event_body_defaults_visibility_to_shared(test_db):
    service = GoogleSyncService(test_db)
    event = Event(
        id="evt-vis-2",
        title="No visibility field",
        description="",
        start_at=datetime(2026, 3, 20, 9, 0, 0),
        end_at=datetime(2026, 3, 20, 10, 0, 0),
        timezone="UTC",
        created_by_user_id="owner-456",
    )
    body = service._event_body(event)
    assert body["extendedProperties"]["private"]["cp_visibility"] == "shared"


def test_extract_cp_visibility_valid():
    ge = {"extendedProperties": {"private": {"cp_visibility": "private"}}}
    assert GoogleSyncService._extract_cp_visibility(ge) == "private"


def test_extract_cp_visibility_unknown_defaults_shared():
    ge = {"extendedProperties": {"private": {"cp_visibility": "unknown"}}}
    assert GoogleSyncService._extract_cp_visibility(ge) == "shared"


def test_extract_cp_visibility_missing_defaults_shared():
    assert GoogleSyncService._extract_cp_visibility({}) == "shared"
    assert GoogleSyncService._extract_cp_visibility({"extendedProperties": {}}) == "shared"
