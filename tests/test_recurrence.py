from datetime import datetime


def test_recurring_event_expands_into_following_month(authenticated_client):
    # Root event in April, weekly 8 times. Expect occurrences in May month grid.
    create_response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Weekly Sync",
            "description": "Recurring",
            "start_at": "2026-04-01T10:00:00",
            "end_at": "2026-04-01T11:00:00",
            "timezone": "UTC",
            "rrule": "FREQ=WEEKLY;COUNT=8",
        },
    )
    assert create_response.status_code == 201

    may_response = authenticated_client.get("/calendar/month?year=2026&month=5")
    assert may_response.status_code == 200
    assert "Weekly Sync" in may_response.text


def test_daily_recurrence_shows_in_day_panel(authenticated_client):
    create_response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Daily Standup",
            "description": "Recurring",
            "start_at": "2026-03-10T09:00:00",
            "end_at": "2026-03-10T09:30:00",
            "timezone": "UTC",
            "rrule": "FREQ=DAILY;COUNT=5",
        },
    )
    assert create_response.status_code == 201

    day_response = authenticated_client.get("/calendar/day?year=2026&month=3&day=12")
    assert day_response.status_code == 200
    assert "Daily Standup" in day_response.text
