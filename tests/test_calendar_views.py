import uuid
from datetime import datetime, timedelta

from app.database.models import Event


def test_month_view_renders_event_title_and_time(authenticated_client):
    now = datetime.utcnow().replace(microsecond=0)
    authenticated_client.post(
        "/api/events",
        json={
            "title": "Gym",
            "description": "Workout",
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "UTC",
        },
    )

    response = authenticated_client.get(f"/calendar/month?year={now.year}&month={now.month}")
    assert response.status_code == 200
    assert "Gym" in response.text


def test_day_view_renders_event(authenticated_client):
    now = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
    authenticated_client.post(
        "/api/events",
        json={
            "title": "Lunch",
            "description": "Cafe",
            "start_at": (now + timedelta(hours=3)).isoformat(),
            "end_at": (now + timedelta(hours=4)).isoformat(),
            "timezone": "UTC",
        },
    )

    response = authenticated_client.get(f"/calendar/day?year={now.year}&month={now.month}&day={now.day}")
    assert response.status_code == 200
    assert "Lunch" in response.text


def test_month_navigation_changes_label(authenticated_client):
    now = datetime.utcnow().replace(microsecond=0)

    current_response = authenticated_client.get(f"/calendar/month?year={now.year}&month={now.month}")
    assert current_response.status_code == 200

    next_month = 1 if now.month == 12 else now.month + 1
    next_year = now.year + 1 if now.month == 12 else now.year

    next_response = authenticated_client.get(f"/calendar/month?year={next_year}&month={next_month}")
    assert next_response.status_code == 200
    assert current_response.text != next_response.text


def test_month_view_ignores_malformed_recurrence_rule(authenticated_client, test_user_a, test_db):
    now = datetime.utcnow().replace(microsecond=0)
    bad_rrule_event = Event(
        id=str(uuid.uuid4()),
        calendar_id=test_user_a.calendar_id,
        created_by_user_id=test_user_a.id,
        last_edited_by_user_id=test_user_a.id,
        title="Broken Recurrence",
        description="Legacy invalid RRULE",
        start_at=now,
        end_at=now + timedelta(hours=1),
        timezone="UTC",
        rrule="NOT_A_VALID_RRULE",
    )
    test_db.add(bad_rrule_event)
    test_db.commit()

    response = authenticated_client.get(f"/calendar/month?year={now.year}&month={now.month}")
    assert response.status_code == 200


def test_day_view_ignores_malformed_recurrence_rule(authenticated_client, test_user_a, test_db):
    now = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
    bad_rrule_event = Event(
        id=str(uuid.uuid4()),
        calendar_id=test_user_a.calendar_id,
        created_by_user_id=test_user_a.id,
        last_edited_by_user_id=test_user_a.id,
        title="Broken Recurrence",
        description="Legacy invalid RRULE",
        start_at=now,
        end_at=now + timedelta(hours=1),
        timezone="UTC",
        rrule="NOT_A_VALID_RRULE",
    )
    test_db.add(bad_rrule_event)
    test_db.commit()

    response = authenticated_client.get(f"/calendar/day?year={now.year}&month={now.month}&day={now.day}")
    assert response.status_code == 200


# ── Quick Add modal (server-rendered HTML presence) ───────────────────────────

def _calendar_html(authenticated_client):
    response = authenticated_client.get("/")
    assert response.status_code == 200
    return response.text


def test_quick_add_modal_opens_on_button_click(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert 'id="qa-open-btn"' in html
    assert "addEventListener('click', openModal)" in html
    assert "qaModal.classList.remove('hidden')" in html
    assert "qaTextInput.focus()" in html


def test_quick_add_parse_successful(authenticated_client):
    response = authenticated_client.post(
        "/api/events/parse",
        json={"text": "dentist tomorrow 2pm", "context_date": "2026-03-19"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"]
    assert data["start_at"] is not None
    assert "errors" in data

    html = _calendar_html(authenticated_client)
    assert "populateReview(text, parsed)" in html
    assert "showPhase('review')" in html
    assert 'id="qa-parsed-title"' in html
    assert 'id="qa-parsed-start"' in html
    assert 'id="qa-parsed-end"' in html


def test_quick_add_parse_error_handling(authenticated_client):
    response = authenticated_client.post(
        "/api/events/parse",
        json={"text": "meeting at 2pm", "context_date": "2026-03-19"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" in data
    assert isinstance(data["errors"], list)

    html = _calendar_html(authenticated_client)
    assert 'id="qa-error-inline"' in html
    assert 'id="qa-error-summary"' in html
    assert "showQAError(" in html
    assert "showPhase('text-entry')" in html


def test_quick_add_save_event(authenticated_client):
    now = datetime.utcnow().replace(microsecond=0)
    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Quick add save",
            "start_at": (now + timedelta(hours=2)).isoformat(),
            "end_at": (now + timedelta(hours=3)).isoformat(),
            "timezone": "UTC",
        },
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Quick add save"

    html = _calendar_html(authenticated_client)
    assert "showToast('Event saved')" in html
    assert "closeModal();" in html
    assert "await refreshPanels();" in html


def test_quick_add_save_and_add_another(authenticated_client):
    now = datetime.utcnow().replace(microsecond=0)
    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Quick add save another",
            "start_at": (now + timedelta(hours=4)).isoformat(),
            "end_at": (now + timedelta(hours=5)).isoformat(),
            "timezone": "UTC",
        },
    )
    assert response.status_code == 201

    html = _calendar_html(authenticated_client)
    assert "if (keepOpen)" in html
    assert "resetModal();" in html
    assert "qaTextInput.focus();" in html


def test_quick_add_escape_closes_modal(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "if (e.key === 'Escape'" in html
    assert "!_saveInFlight" in html
    assert "closeModal();" in html


def test_quick_add_back_button(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "qa-back-btn" in html
    assert "addEventListener('click', () =>" in html
    assert "showPhase('text-entry')" in html
    assert "qaTextInput.focus();" in html


def test_quick_add_edit_review_fields(authenticated_client):
    now = datetime.utcnow().replace(microsecond=0)
    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "dentist appointment",
            "start_at": (now + timedelta(days=1, hours=1)).isoformat(),
            "end_at": (now + timedelta(days=1, hours=2)).isoformat(),
            "timezone": "UTC",
            "rrule": "FREQ=WEEKLY;COUNT=3",
        },
    )
    assert response.status_code == 201
    event = response.json()
    assert event["title"] == "dentist appointment"
    assert event["rrule"] == "FREQ=WEEKLY;COUNT=3"

    html = _calendar_html(authenticated_client)
    assert 'id="qa-parsed-title"' in html
    assert 'id="qa-parsed-repeat"' in html
    assert 'id="qa-save-btn"' in html
