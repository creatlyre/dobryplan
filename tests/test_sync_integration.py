def test_event_create_triggers_sync(authenticated_client, monkeypatch):
    called = {"count": 0, "deleted": None}

    class FakeResult:
        users_synced = 1
        events_synced = 1
        errors = []

    def fake_sync(self, event, deleted=False):
        called["count"] += 1
        called["deleted"] = deleted
        return FakeResult()

    import app.sync.service

    monkeypatch.setattr(app.sync.service.GoogleSyncService, "sync_event_for_household", fake_sync)

    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Sync Test",
            "description": None,
            "start_at": "2026-03-18T10:00:00",
            "end_at": "2026-03-18T11:00:00",
            "timezone": "UTC",
        },
    )

    assert response.status_code == 201
    assert called["count"] == 1
    assert called["deleted"] is False


def test_event_delete_triggers_delete_sync(authenticated_client, monkeypatch):
    called = {"count": 0, "deleted": None}

    class FakeResult:
        users_synced = 1
        events_synced = 1
        errors = []

    def fake_sync(self, event, deleted=False):
        called["count"] += 1
        called["deleted"] = deleted
        return FakeResult()

    import app.sync.service

    monkeypatch.setattr(app.sync.service.GoogleSyncService, "sync_event_for_household", fake_sync)

    create_response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Delete Sync",
            "description": None,
            "start_at": "2026-03-18T12:00:00",
            "end_at": "2026-03-18T13:00:00",
            "timezone": "UTC",
        },
    )
    event_id = create_response.json()["id"]

    delete_response = authenticated_client.delete(f"/api/events/{event_id}")
    assert delete_response.status_code == 200
    assert called["count"] >= 2
    assert called["deleted"] is True


def test_private_event_sync_only_targets_owner(authenticated_client, monkeypatch):
    """Private event should still trigger sync, but the sync service
    filters recipients internally. Here we just verify sync is called."""
    called = {"events": []}

    class FakeResult:
        users_synced = 1
        events_synced = 1
        errors = []

    def fake_sync(self, event, deleted=False):
        called["events"].append({"visibility": getattr(event, "visibility", "shared"), "deleted": deleted})
        return FakeResult()

    import app.sync.service
    monkeypatch.setattr(app.sync.service.GoogleSyncService, "sync_event_for_household", fake_sync)

    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Secret dentist",
            "description": None,
            "start_at": "2026-03-18T10:00:00",
            "end_at": "2026-03-18T11:00:00",
            "timezone": "UTC",
            "visibility": "private",
        },
    )
    assert response.status_code == 201
    assert called["events"][0]["visibility"] == "private"


def test_shared_event_sync_targets_all_household(authenticated_client, monkeypatch):
    called = {"events": []}

    class FakeResult:
        users_synced = 2
        events_synced = 1
        errors = []

    def fake_sync(self, event, deleted=False):
        called["events"].append({"visibility": getattr(event, "visibility", "shared")})
        return FakeResult()

    import app.sync.service
    monkeypatch.setattr(app.sync.service.GoogleSyncService, "sync_event_for_household", fake_sync)

    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Family BBQ",
            "description": None,
            "start_at": "2026-03-18T12:00:00",
            "end_at": "2026-03-18T14:00:00",
            "timezone": "UTC",
            "visibility": "shared",
        },
    )
    assert response.status_code == 201
    assert called["events"][0]["visibility"] == "shared"
