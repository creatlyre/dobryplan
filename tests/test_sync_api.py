from datetime import datetime
from types import SimpleNamespace

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


def test_event_body_includes_default_popup_reminder(test_db):
    service = GoogleSyncService(test_db)
    event = SimpleNamespace(
        id="evt-1",
        title="Reminder event",
        description="",
        start_at=datetime(2026, 3, 20, 9, 0, 0),
        end_at=datetime(2026, 3, 20, 10, 0, 0),
        timezone="UTC",
        rrule=None,
    )

    body = service._event_body(event)

    assert "reminders" in body
    assert body["reminders"]["useDefault"] is False
    assert body["reminders"]["overrides"][0]["method"] == "popup"
    assert body["reminders"]["overrides"][0]["minutes"] > 0


def test_event_body_uses_per_event_reminder_minutes(test_db):
    service = GoogleSyncService(test_db)
    event = SimpleNamespace(
        id="evt-2",
        title="Custom reminder",
        description="",
        start_at=datetime(2026, 3, 20, 11, 0, 0),
        end_at=datetime(2026, 3, 20, 12, 0, 0),
        timezone="UTC",
        rrule=None,
        reminder_minutes=5,
    )

    body = service._event_body(event)
    assert body["reminders"]["overrides"][0]["minutes"] == 5
