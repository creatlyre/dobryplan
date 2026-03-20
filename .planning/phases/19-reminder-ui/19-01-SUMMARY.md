---
phase: 19-reminder-ui
plan: 01
subsystem: ui
tags: [reminders, i18n, jinja2, javascript, chips-ui]

requires:
  - phase: 18-event-privacy
    provides: visibility field in event forms and day_events template
provides:
  - Reminder i18n keys (en + pl) for toggle, chips, add/remove, sync help
  - Reminder HTML sections in event_entry_modal.html and event_form.html
  - JavaScript chip rendering, add/remove, toggle, edit prefill, submit payload
  - Edit button passes reminder_minutes_list to prefillEvent
affects: [sync, events]

tech-stack:
  added: []
  patterns: [chip-based multi-value UI with add/remove, toggle-controlled form sections]

key-files:
  created: []
  modified:
    - app/locales/en.json
    - app/locales/pl.json
    - app/templates/partials/event_entry_modal.html
    - app/templates/partials/event_form.html
    - app/templates/calendar.html
    - app/templates/partials/day_events.html

key-decisions:
  - "Default reminders set to 30min and 2 days (2880min) for new events"
  - "Method select (popup/email) is visual-only — backend hardcodes popup for Google sync"
  - "Max 5 reminders enforced client-side with counter text"

patterns-established:
  - "Chip UI: inline-flex rounded-full elements with × remove buttons"
  - "Toggle-controlled sections: checkbox toggles container visibility"

requirements-completed: [REM-01, REM-02, REM-03]

duration: 3min
completed: 2026-03-20
---

# Phase 19 Plan 01: Reminder UI Summary

**Chip-based reminder controls wired into event forms with toggle, add/remove, edit prefill, and API payload integration**

## What Was Built

### Task 1: i18n Keys and HTML Sections
- Added 11 `reminder.*` i18n keys to both `en.json` and `pl.json`
- Added reminder section to `event_entry_modal.html` with toggle, chip container, add row (minutes input + method select + confirm), add button, counter, and sync help text
- Added matching reminder section to `event_form.html` with `event-reminder-*` IDs for form parity

**Commit:** `c05a909` feat(19-01): add reminder i18n keys and HTML sections

### Task 2: JavaScript Wiring
- Added 4 I18N entries for reminder toggle/max/remove labels
- Added 11 DOM refs for all reminder elements
- Implemented `renderReminderChips()`, `formatReminderMinutes()`, `updateReminderAddState()`, `setRemindersEnabled()`
- Wired toggle, add button, and confirm button event listeners
- Updated `resetEventEntryForm()` to reset reminders to defaults (30min + 2 days)
- Updated `prefillEvent()` to accept 7th argument (`reminderMinutesList`) and populate reminder state
- Added `reminder_minutes_list` to `submitEventEntry()` payload (array if enabled, empty if toggled off)
- Updated `day_events.html` edit button to pass `event.reminder_minutes_list` as 7th argument

**Commit:** `3dae7fc` feat(19-01): wire reminder JavaScript — chips, add/remove, edit prefill, payload

## Deviations from Plan

None — plan executed exactly as written.

## Verification

- All i18n keys parse correctly in both locales
- All HTML elements present in both templates
- All JS functions and DOM refs verified
- 232 backend tests pass with zero regressions
