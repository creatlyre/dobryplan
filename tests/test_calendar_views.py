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


# ── Year disambiguation (05-05) ────────────────────────────────────────────

def test_quick_add_parse_returns_ambiguity_metadata(authenticated_client):
    """Parser returns ambiguous flag and year candidates for month/day without explicit year."""
    # "december 25" from context 2026-03-19 → Dec 25 2026 is in future → ambiguous
    response = authenticated_client.post(
        "/api/events/parse",
        json={"text": "doctor appointment december 25", "context_date": "2026-03-19"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "ambiguous" in data
    assert data["ambiguous"] is True
    assert "year_candidates" in data
    assert 2026 in data["year_candidates"]
    assert 2027 in data["year_candidates"]


def test_quick_add_ambiguity_phase_markup(authenticated_client):
    """Calendar page includes disambiguation phase section in quick-add modal."""
    html = _calendar_html(authenticated_client)
    assert 'id="qa-ambiguity-phase"' in html
    assert 'id="qa-ambiguity-event-summary"' in html


def test_quick_add_year_choice_controls(authenticated_client):
    """Calendar page includes container for dynamically rendered year choice buttons."""
    html = _calendar_html(authenticated_client)
    assert 'id="qa-year-choice-container"' in html
    assert 'id="qa-ambiguity-back-btn"' in html


def test_quick_add_ambiguity_state_handling(authenticated_client):
    """JS state machine routes to ambiguity phase when parse result carries ambiguous flag."""
    html = _calendar_html(authenticated_client)
    assert "_ambiguityPending" in html
    assert "parsed.ambiguous" in html
    assert "showPhase('ambiguity')" in html
    assert "selectAmbiguousYear" in html


def test_quick_add_save_gated_on_unresolved_ambiguity(authenticated_client):
    """Save action checks _ambiguityPending and blocks save until year is chosen."""
    html = _calendar_html(authenticated_client)
    assert "if (_ambiguityPending)" in html


# ── OCR quick-add flow (06-01) ────────────────────────────────────────────

def test_quick_add_ocr_controls_present(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert 'id="qa-ocr-btn"' in html
    assert 'id="qa-ocr-input"' in html
    assert "Scan Image" in html


def test_quick_add_ocr_endpoint_wiring(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "parseFromImage(file)" in html
    assert "fetch('/api/events/ocr-parse'" in html
    assert "OCR confidence:" in html


def test_quick_add_ocr_fallback_on_errors(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "parsed.raw_text || 'No readable text extracted.'" in html
    assert "showPhase('fallback')" in html


# ── Google sync panel (07-xx revisit) ─────────────────────────────────────

def test_google_sync_panel_present(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "Google Sync" in html
    assert 'id="sync-status"' in html
    assert 'id="sync-last-success"' in html
    assert 'id="sync-refresh-btn"' in html
    assert 'id="sync-export-btn"' in html
    assert 'id="sync-import-btn"' in html
    assert 'id="sync-connect-link"' in html


def test_google_sync_panel_wiring(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "fetch('/api/sync/status')" in html
    assert "fetch(`/api/sync/export-month?year=${currentYear}&month=${currentMonth}`" in html
    assert "fetch(`/api/sync/import-month?year=${currentYear}&month=${currentMonth}`" in html
    assert "formatSyncTimestamp" in html
    assert "Last successful sync:" in html
    assert "loadSyncStatus();" in html
    assert "syncRefreshBtn.addEventListener('click', loadSyncStatus)" in html
    assert "syncExportBtn.addEventListener('click', exportCurrentMonthToGoogle)" in html
    assert "syncImportBtn.addEventListener('click', importCurrentMonthFromGoogle)" in html
    assert "No events found for this month" in html
    assert "calendars_scanned" in html


# ── Phase 7 UI/UX modal flow ──────────────────────────────────────────────

def test_event_entry_modal_markup_present(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert 'id="event-entry-open-btn"' in html
    assert 'id="event-entry-modal"' in html
    assert 'id="event-entry-form"' in html
    assert 'id="event-entry-title-input"' in html
    assert 'id="event-entry-start-date"' in html
    assert 'id="event-entry-start-time"' in html
    assert 'id="event-entry-end-time"' in html


def test_event_entry_modal_validation_and_submit_markers(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "updateEventEntryValidation" in html
    assert "eventEntrySaveBtn.disabled" in html
    assert "eventEntrySaveAnotherBtn.disabled" in html
    assert "autoCorrectEndDateTime" in html
    assert "submitEventEntry" in html
    assert "eventEntrySaveError" in html


def test_event_entry_keyboard_routing_markers(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "closeEventEntryModal" in html
    assert "openEventEntryModal" in html
    assert "Escape closes topmost visible modal" in html
    assert "E opens manual event-entry modal only outside typing contexts." in html


def test_quick_add_manual_entry_bridge_present(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert 'id="qa-manual-btn"' in html
    assert "openManualFromQuickAdd" in html
    assert "qaManualBtn.addEventListener('click'" in html


def test_event_entry_mobile_fullscreen_markers(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "#event-entry-modal" in html
    assert "#event-entry-panel" in html
    assert "min-height: 100vh" in html
    assert "max-width: 100%" in html


def test_day_click_opens_event_entry_for_selected_day(authenticated_client):
    month = authenticated_client.get("/calendar/month?year=2026&month=3")
    assert month.status_code == 200
    assert "openEventEntryForDay(" in month.text

    html = _calendar_html(authenticated_client)
    assert "function openEventEntryForDay(year, month, day)" in html
    assert "Date locked to selected calendar day." in html
    assert "setEventEntryDateLocked(true)" in html


def test_invite_back_link_present(authenticated_client):
    response = authenticated_client.get("/invite")
    assert response.status_code == 200
    html = response.text
    assert 'href="/calendar"' in html
    assert "Back to Calendar" in html
    assert "focus-visible:ring-cyan-300" in html
