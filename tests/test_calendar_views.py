import uuid
from datetime import datetime, timedelta

from app.database.models import Event


def assert_contains_any(text: str, *candidates: str) -> None:
    assert any(candidate in text for candidate in candidates), (
        f"Expected one of {candidates} to be present"
    )


def assert_locale_rendered(html_text, expected_locale):
    """Verify locale identifier in page (e.g., 'pl-PL', Polish label)."""
    if expected_locale == "pl":
        assert 'lang="pl"' in html_text or "Wyloguj" in html_text  # Polish logout
    elif expected_locale == "en":
        assert 'lang="en"' in html_text or "Logout" in html_text  # English logout


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
    assert "showToast(I18N.eventSaved)" in html
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


# ── Day-click quick-entry mode ────────────────────────────────────────────────


def test_day_click_opens_quick_entry_modal(authenticated_client):
    """Verify day-click on calendar day loads the day view."""
    now = datetime.utcnow()

    # Main page has the addEventForDay function (available for programmatic use)
    html = _calendar_html(authenticated_client)
    assert "addEventForDay" in html, "Calendar must have addEventForDay function"
    assert "calculateEndTime" in html, "Calendar must have calculateEndTime function"
    assert "getDefaultStartTime" in html, "Calendar must have getDefaultStartTime function"
    assert "setEventEntryDateLocked(true)" in html, "addEventForDay must lock the date field"

    # Month grid endpoint has day cells with data attributes
    response = authenticated_client.get(
        f"/calendar/month?year={now.year}&month={now.month}"
    )
    assert response.status_code == 200
    grid_html = response.text
    assert "data-day" in grid_html, "Month grid day cells must have data-day attributes"
    assert "data-year" in grid_html, "Month grid day cells must have data-year attributes"
    assert "data-month" in grid_html, "Month grid day cells must have data-month attributes"
    assert "loadDay(" in grid_html, "Day cells must call loadDay on click"


def test_quick_entry_saves_with_auto_end_time(authenticated_client):
    """Verify quick-entry saves event with auto-calculated end-time +1h from start."""
    now = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)

    start = now + timedelta(hours=2)
    end = start + timedelta(hours=1)
    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Quick add test",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "timezone": "UTC",
        },
    )
    assert response.status_code == 201
    event = response.json()

    assert event.get("end_at") is not None, "Event must have end_at set"

    start_time = datetime.fromisoformat(event["start_at"])
    end_time = datetime.fromisoformat(event["end_at"])
    delta = end_time - start_time
    assert delta.total_seconds() == 3600, (
        f"End time must be 1 hour after start, got {delta.total_seconds()}s"
    )

    # Verify auto-calculation JS exists on the client
    html = _calendar_html(authenticated_client)
    assert "calculateEndTime" in html
    assert "quick-entry-mode" in html


def test_quick_entry_mode_locks_date_field(authenticated_client):
    """Verify event-entry form has quick-entry-mode class and date field shows lock indicator."""
    html = _calendar_html(authenticated_client)

    # Quick-entry styling class exists in CSS/JS
    assert "quick-entry-mode" in html, "Event form must have quick-entry-mode class for styling"

    # Quick-entry hint exists in modal
    assert "quick-entry-hint" in html, "Modal should have quick-entry hint for user awareness"

    # Date-lock indicator is in modal
    assert "date-lock-note" in html.lower() or "date_locked" in html.lower(), (
        "Modal should indicate date is locked"
    )
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
    assert_contains_any(html, "Scan Image", "Skanuj obraz")


def test_quick_add_ocr_endpoint_wiring(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "parseFromImage(file)" in html
    assert "fetch('/api/events/ocr-parse'" in html
    assert "OCR confidence:" in html


def test_quick_add_ocr_fallback_on_errors(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "parsed.raw_text ||" in html
    assert "showPhase('fallback')" in html


# ── Google sync panel (07-xx revisit) ─────────────────────────────────────

def test_google_sync_panel_present(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert_contains_any(html, "Google Sync", "Synchronizacja Google")
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
    assert "syncLastPrefix" in html
    assert "loadSyncStatus();" in html
    assert "syncRefreshBtn.addEventListener('click', loadSyncStatus)" in html
    assert "syncExportBtn.addEventListener('click', exportCurrentMonthToGoogle)" in html
    assert "syncImportBtn.addEventListener('click', importCurrentMonthFromGoogle)" in html
    assert "syncPullEmpty" in html
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
    assert "loadDay(" in month.text

    html = _calendar_html(authenticated_client)
    assert "function addEventForDay(year, month, day)" in html
    assert_contains_any(html, "Date locked to selected calendar day.", "Data zablokowana na wybranym dniu kalendarza.")
    assert "setEventEntryDateLocked(true)" in html


def test_invite_back_link_present(authenticated_client):
    response = authenticated_client.get("/invite")
    assert response.status_code == 200
    html = response.text
    assert 'href="/calendar"' in html
    assert_contains_any(html, "Back to Calendar", "Powrot do kalendarza", "Powr\u00f3t do kalendarza")
    assert "focus-visible:ring-cyan-300" in html


# ── Phase 8 visibility controls ───────────────────────────────────────────


def test_event_entry_visibility_control_present(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert 'id="event-entry-visibility"' in html
    assert_contains_any(html, "Shared (household)", "Wspolne (domownicy)", "Wsp\u00f3lne (domownicy)")
    assert_contains_any(html, "Private (only me)", "Prywatne (tylko ja)")
    assert 'value="shared"' in html
    assert 'value="private"' in html


def test_quick_add_visibility_control_present(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert 'id="qa-parsed-visibility"' in html
    assert_contains_any(html, "Shared (household)", "Wspolne (domownicy)", "Wsp\u00f3lne (domownicy)")
    assert_contains_any(html, "Private (only me)", "Prywatne (tylko ja)")


def test_event_entry_submit_includes_visibility(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "visibility: eventEntryVisibilityInput.value" in html


def test_quick_add_payload_includes_visibility(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "visibility: document.getElementById('qa-parsed-visibility').value" in html


def test_quick_add_clear_review_resets_visibility(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "qa-parsed-visibility" in html
    assert "vis.value = 'shared'" in html


def test_prefill_event_accepts_visibility(authenticated_client):
    html = _calendar_html(authenticated_client)
    assert "eventEntryVisibilityInput.value = visibility || 'shared'" in html


# ── Phase 9 locale and language switching ─────────────────────────────────────

def test_default_locale_is_polish(authenticated_client):
    """First-time user sees Polish UI by default."""
    html = authenticated_client.get("/").text
    assert_locale_rendered(html, "pl")
    # Check some Polish copy is present
    assert_contains_any(html, "Kalendarz", "Wyloguj", "Synchronizacja Google")


def test_switch_locale_from_polish_to_english(authenticated_client):
    """User can switch to English and UI updates."""
    # Load in English
    html = authenticated_client.get("/?lang=en").text
    assert_locale_rendered(html, "en")
    assert_contains_any(html, "Calendar", "Logout", "Google Sync")


def test_locale_cookie_persists_across_reload(authenticated_client):
    """Language selection persists in cookie across page reload."""
    # Switch to English
    response1 = authenticated_client.get("/?lang=en")
    assert response1.status_code == 200

    # Verify cookie was set
    cookies = authenticated_client.cookies
    assert cookies.get("locale") == "en"

    # Reload without query param
    html = authenticated_client.get("/").text
    assert_locale_rendered(html, "en")  # Should still be English


def test_english_locale_consistent_across_pages(authenticated_client):
    """English rendering is consistent across different pages."""
    # Set locale to English
    authenticated_client.get("/?lang=en")

    # Check calendar page
    calendar_html = authenticated_client.get("/").text
    assert_contains_any(calendar_html, "Calendar", "Logout", "Google Sync")

    # Check invite page
    invite_html = authenticated_client.get("/invite").text
    assert_contains_any(invite_html, "Back to Calendar", "Logout")


def test_query_param_overrides_cookie(authenticated_client):
    """?lang=en overrides persisted pl cookie."""
    # Set cookie to Polish
    authenticated_client.get("/?lang=pl")
    assert authenticated_client.cookies.get("locale") == "pl"

    # Request with ?lang=en should set new cookie
    html = authenticated_client.get("/?lang=en").text
    assert_locale_rendered(html, "en")
    assert authenticated_client.cookies.get("locale") == "en"


# ── Phase 11 Wave 3: Backward compatibility regression ────────────────────────


def test_manual_event_entry_full_form_still_works(authenticated_client):
    """Regression: traditional full-form event creation unchanged by day-click additions."""
    now = datetime.utcnow().replace(microsecond=0)

    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Full form event",
            "description": "Created via traditional full manual form",
            "start_at": (now + timedelta(hours=5)).isoformat(),
            "end_at": (now + timedelta(hours=6)).isoformat(),
            "timezone": "UTC",
            "visibility": "private",
            "rrule": "FREQ=DAILY;COUNT=3",
        },
    )
    assert response.status_code == 201
    event = response.json()
    assert event["title"] == "Full form event"
    assert event["description"] == "Created via traditional full manual form"
    assert event["visibility"] == "private"
    assert event["rrule"] == "FREQ=DAILY;COUNT=3"

    response = authenticated_client.get(
        f"/calendar/month?year={now.year}&month={now.month}"
    )
    assert response.status_code == 200
    assert "Full form event" in response.text


def test_recurring_event_creation_unchanged(authenticated_client):
    """Regression: recurring event creation still works with full params."""
    now = datetime.utcnow().replace(microsecond=0)

    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Weekly meeting",
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "UTC",
            "rrule": "FREQ=WEEKLY;UNTIL=20260630",
        },
    )
    assert response.status_code == 201
    event = response.json()
    assert event["rrule"] == "FREQ=WEEKLY;UNTIL=20260630"
    assert "Weekly meeting" in event["title"]


def test_event_deletion_unchanged(authenticated_client, test_db, test_user_a):
    """Regression: event deletion still works."""
    now = datetime.utcnow().replace(microsecond=0)

    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "To delete",
            "start_at": (now + timedelta(hours=2)).isoformat(),
            "end_at": (now + timedelta(hours=3)).isoformat(),
            "timezone": "UTC",
        },
    )
    assert response.status_code == 201
    event_id = response.json()["id"]

    response = authenticated_client.delete(f"/api/events/{event_id}")
    assert response.status_code in (200, 204)


def test_sync_export_includes_reminders_backward_compat(
    authenticated_client, test_db, test_user_a,
):
    """Regression: old single-reminder field still handled correctly in sync payload."""
    from app.sync.service import GoogleSyncService
    from app.events.repository import EventRepository

    now = datetime.utcnow().replace(microsecond=0)

    response = authenticated_client.post(
        "/api/events",
        json={
            "title": "Single reminder event",
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "UTC",
            "reminder_minutes": 15,
        },
    )
    assert response.status_code == 201

    service = GoogleSyncService(test_db)
    event = EventRepository(test_db).get_by_id(
        response.json()["id"], test_user_a.calendar_id,
    )
    body = service._event_body(event)

    assert body["reminders"]["useDefault"] is False
    assert len(body["reminders"]["overrides"]) == 1
    assert body["reminders"]["overrides"][0]["minutes"] == 15


# ── Phase 18 Nyquist: event privacy template validation ───────────────────────


def test_month_grid_lock_icon_for_private_event(authenticated_client):
    """VIS-03: Private events display 🔒 before title in month grid."""
    now = datetime.utcnow().replace(microsecond=0)
    authenticated_client.post(
        "/api/events",
        json={
            "title": "PrivMonthEvt",
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "UTC",
            "visibility": "private",
        },
    )
    html = authenticated_client.get(
        f"/calendar/month?year={now.year}&month={now.month}"
    ).text
    assert "PrivMonthEvt" in html
    assert "🔒" in html, "Lock icon must appear for private event in month grid"


def test_month_grid_no_lock_icon_for_shared_event(authenticated_client):
    """VIS-03: Shared events do NOT display 🔒 in month grid."""
    now = datetime.utcnow().replace(microsecond=0)
    authenticated_client.post(
        "/api/events",
        json={
            "title": "SharedMonthEvt",
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "UTC",
            "visibility": "shared",
        },
    )
    html = authenticated_client.get(
        f"/calendar/month?year={now.year}&month={now.month}"
    ).text
    assert "SharedMonthEvt" in html
    # Find the event cell text — lock should not appear near the shared event title
    idx = html.index("SharedMonthEvt")
    snippet = html[max(0, idx - 80):idx]
    assert "🔒" not in snippet, "Lock icon must NOT appear for shared events in month grid"


def test_day_view_lock_icon_for_private_event(authenticated_client):
    """VIS-03: Private events display 🔒 before title in day view."""
    now = datetime.utcnow().replace(microsecond=0)
    authenticated_client.post(
        "/api/events",
        json={
            "title": "PrivDayEvt",
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "UTC",
            "visibility": "private",
        },
    )
    html = authenticated_client.get(
        f"/calendar/day?year={now.year}&month={now.month}&day={now.day}"
    ).text
    assert "PrivDayEvt" in html
    assert "🔒" in html, "Lock icon must appear for private event in day view"


def test_event_form_visibility_dropdown_present():
    """VIS-01: Simple event form (event_form.html) has visibility dropdown."""
    import pathlib
    html = pathlib.Path("app/templates/partials/event_form.html").read_text(encoding="utf-8")
    assert 'id="event-visibility"' in html, "event_form.html must have visibility select"
    assert 'value="shared"' in html
    assert 'value="private"' in html
    assert "qa.visibility" in html, "Visibility label must use i18n key"


# ── Phase 19: Reminder UI Nyquist validation ──────────────────────────────────


def test_reminder_i18n_keys_complete_in_both_locales():
    """All 11 reminder.* i18n keys must exist in both en.json and pl.json."""
    import json
    from pathlib import Path

    locales_dir = Path(__file__).resolve().parent.parent / "app" / "locales"
    expected_keys = [
        "reminder.label",
        "reminder.toggle_on",
        "reminder.toggle_off",
        "reminder.add",
        "reminder.method_popup",
        "reminder.method_email",
        "reminder.minutes_placeholder",
        "reminder.method_label",
        "reminder.sync_help",
        "reminder.max_reached",
        "reminder.remove_label",
    ]

    for locale_file in ["en.json", "pl.json"]:
        with open(locales_dir / locale_file, encoding="utf-8") as f:
            data = json.load(f)
        for key in expected_keys:
            assert key in data, f"Missing i18n key '{key}' in {locale_file}"
            assert data[key].strip(), f"Empty i18n value for '{key}' in {locale_file}"


def test_reminder_ui_elements_in_event_entry_modal(authenticated_client):
    """Rendered calendar page contains all reminder DOM elements in event entry modal."""
    html = _calendar_html(authenticated_client)
    assert 'id="event-entry-reminders-toggle"' in html
    assert 'id="event-entry-reminder-chips"' in html
    assert 'id="event-entry-reminder-add-btn"' in html
    assert 'id="event-entry-reminder-counter"' in html
    assert "renderReminderChips" in html
    assert "formatReminderMinutes" in html


# ── ECAT-03: Color-coded month grid and day view indicators ──────────────────


def test_month_grid_renders_category_dot_for_categorized_event(authenticated_client):
    """ECAT-03: Month grid event pills include category-dot span with color."""
    now = datetime.utcnow().replace(microsecond=0)
    # Get preset categories (lazy-seeded)
    cat_resp = authenticated_client.get("/api/events/categories")
    cats = cat_resp.json()
    work_cat = next(c for c in cats if c["name"] == "Work")

    # Create event with Work category
    authenticated_client.post(
        "/api/events",
        json={
            "title": "Phase 23 Test",
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "UTC",
            "category_id": work_cat["id"],
        },
    )

    html = authenticated_client.get(f"/calendar/month?year={now.year}&month={now.month}").text
    assert "category-dot" in html
    assert work_cat["color"] in html
    assert f'data-category-id="{work_cat["id"]}"' in html


def test_day_view_renders_category_color_indicator(authenticated_client):
    """ECAT-03: Day event list shows category color left-border and name badge."""
    now = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
    cat_resp = authenticated_client.get("/api/events/categories")
    health_cat = next(c for c in cat_resp.json() if c["name"] == "Health")

    authenticated_client.post(
        "/api/events",
        json={
            "title": "Morning Run",
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "UTC",
            "category_id": health_cat["id"],
        },
    )

    html = authenticated_client.get(f"/calendar/day?year={now.year}&month={now.month}&day={now.day}").text
    assert "category-color" in html
    assert health_cat["color"] in html
    assert "Health" in html
    assert f'data-category-id="{health_cat["id"]}"' in html


# ── ECAT-04: Category filter UI ─────────────────────────────────────────────


def test_category_filter_bar_rendered_on_calendar_page(authenticated_client):
    """ECAT-04: Calendar page includes category filter bar with JS functions."""
    html = _calendar_html(authenticated_client)
    assert 'id="category-filter"' in html
    assert 'id="category-filter-buttons"' in html
    assert "loadCategories" in html
    assert "toggleCategoryFilter" in html
    assert "applyCategoryFilter" in html
    assert "renderCategoryFilterButtons" in html


# ── ECAT-05: Category selector in event create and edit forms ────────────────


def test_category_dropdown_in_event_entry_modal(authenticated_client):
    """ECAT-05: Event entry modal includes category select dropdown."""
    html = _calendar_html(authenticated_client)
    assert 'id="event-entry-category"' in html
    assert "populateCategoryDropdowns" in html


def test_category_dropdown_in_event_form(authenticated_client):
    """ECAT-05: Simple event form partial includes category select dropdown."""
    import os
    form_path = os.path.join("app", "templates", "partials", "event_form.html")
    with open(form_path, "r", encoding="utf-8") as f:
        html = f.read()
    assert 'id="event-category"' in html


def test_event_submit_includes_category_id_in_payload(authenticated_client):
    """ECAT-05: submitEventEntry JS sends category_id in payload."""
    html = _calendar_html(authenticated_client)
    assert "category_id" in html
    assert "event-entry-category" in html


def test_edit_prefill_passes_category_id(authenticated_client):
    """ECAT-05: day_events edit button passes category_id to prefillEvent."""
    now = datetime.utcnow().replace(hour=14, minute=0, second=0, microsecond=0)
    cat_resp = authenticated_client.get("/api/events/categories")
    personal_cat = next(c for c in cat_resp.json() if c["name"] == "Personal")

    authenticated_client.post(
        "/api/events",
        json={
            "title": "Reading Time",
            "start_at": (now + timedelta(hours=1)).isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "UTC",
            "category_id": personal_cat["id"],
        },
    )

    html = authenticated_client.get(f"/calendar/day?year={now.year}&month={now.month}&day={now.day}").text
    # Verify the edit button onclick passes category_id
    assert personal_cat["id"] in html
