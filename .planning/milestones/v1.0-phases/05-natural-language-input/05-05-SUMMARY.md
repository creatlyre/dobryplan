---
phase: 05-natural-language-input
plan: 05
subsystem: quick-add-modal
tags: [nlp, disambiguation, ux, frontend, tdd]
dependency_graph:
  requires: [05-04]
  provides: [year-disambiguation-ui, ambiguity-metadata-api]
  affects: [app/events/nlp.py, app/events/routes.py, app/templates/calendar.html, app/templates/partials/quick_add_modal.html, tests/test_calendar_views.py]
tech_stack:
  added: []
  patterns: [tdd-red-green, modal-state-machine, api-metadata-extension]
key_files:
  created: []
  modified:
    - app/events/nlp.py
    - app/events/routes.py
    - app/templates/partials/quick_add_modal.html
    - app/templates/calendar.html
    - tests/test_calendar_views.py
decisions:
  - "ambiguous flag emitted only when month/day date is still in future (both years plausible); past month/day silently rolls to next year"
  - "_ambiguityPending flag gates saveEvent until year selection is made; showPhase('ambiguity') re-shown if save attempted early"
  - "Year choice buttons rendered dynamically from year_candidates array; selectAmbiguousYear() clones parsed data and applies setFullYear before populateReview"
  - "[Rule 2 - Missing critical functionality] nlp.py and routes.py updated to return ambiguous + year_candidates; plan files_modified listed only templates but backend metadata is required for UI to function"
metrics:
  duration_minutes: 35
  completed_date: "2026-03-19"
  tasks_completed: 2
  files_changed: 5
---

# Phase 05 Plan 05: Year Disambiguation Quick-Add UI Summary

**One-liner:** Ambiguity confirmation step added to quick-add modal with explicit "Did you mean 2026 or 2027?" year-choice before save, backed by nlp.py ambiguity metadata.

---

## What Was Built

### Task 1 (TDD RED): Failing disambiguation tests
- Added 5 new tests to `tests/test_calendar_views.py` under `# Year disambiguation (05-05)`:
  - `test_quick_add_parse_returns_ambiguity_metadata` — API asserts `ambiguous=True` + `year_candidates=[2026,2027]` for future month/day
  - `test_quick_add_ambiguity_phase_markup` — HTML asserts `#qa-ambiguity-phase` and `#qa-ambiguity-event-summary`
  - `test_quick_add_year_choice_controls` — HTML asserts `#qa-year-choice-container` and `#qa-ambiguity-back-btn`
  - `test_quick_add_ambiguity_state_handling` — JS asserts `_ambiguityPending`, `parsed.ambiguous`, `showPhase('ambiguity')`, `selectAmbiguousYear`
  - `test_quick_add_save_gated_on_unresolved_ambiguity` — JS asserts `if (_ambiguityPending)` gate
- All 5 tests confirmed failing before implementation (RED phase).

### Task 2 (TDD GREEN): Implementation

**app/events/nlp.py:**
- `ParseResult` gains `ambiguous: bool = False` and `year_candidates: list[int]` fields
- `_parse_month_day()` now returns `ambiguous=True` with `year_candidates=[current_year, next_year]` when month/day date is still in future; when current year is past, rolls to next year silently (no ambiguity)
- `parse()` method copies `ambiguous` and `year_candidates` from `parsed_dates` dict into `ParseResult`

**app/events/routes.py:**
- `ParseEventResponse` gains `ambiguous: bool = False` and `year_candidates: list[int] = []`
- Parse endpoint return now includes both fields

**app/templates/partials/quick_add_modal.html:**
- Added `#qa-ambiguity-phase` section between loading and review phases
- Contains amber info box with `#qa-ambiguity-event-summary` span
- Contains `#qa-year-choice-container` for dynamically rendered year buttons
- Contains `#qa-ambiguity-back-btn` to return to text entry

**app/templates/calendar.html:**
- `qaAmbiguity` DOM reference added to IIFE init section
- Three new state variables: `_ambiguityPending`, `_ambiguousParseData`, `_ambiguousOriginalText`
- `resetModal()` clears all three ambiguity state variables
- `showPhase()` updated to toggle `qa-ambiguity-phase` alongside existing phases
- New `selectAmbiguousYear(year)` function: clears `_ambiguityPending`, clones parsed data, applies `setFullYear(year)` to start/end, calls `populateReview()` then `showPhase('review')`
- Parse click handler: after successful parse with `parsed.ambiguous === true`, dynamically renders year-choice buttons and calls `showPhase('ambiguity')` instead of going directly to review
- `saveEvent()` checks `if (_ambiguityPending)` at entry; re-shows ambiguity phase and displays save error if triggered prematurely
- `#qa-ambiguity-back-btn` event listener resets ambiguity state and returns to text entry

---

## Test Results

```
18 passed in tests/test_calendar_views.py (13 disambiguation+quick_add, 5 others)
0 failures, 0 errors
```

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Backend ambiguity metadata added**
- **Found during:** Task 2 implementation
- **Issue:** Plan `files_modified` listed only templates and tests, but UI disambiguation requires parser to return `ambiguous` and `year_candidates` fields
- **Fix:** Extended `ParseResult` dataclass, updated `_parse_month_day()` logic, and extended `ParseEventResponse` Pydantic model to expose fields through the API
- **Files modified:** `app/events/nlp.py`, `app/events/routes.py`
- **Commits:** eede3ae

**2. [Rule 1 - Bug] Indentation error in nlp.py try block**
- **Found during:** Task 2 (syntax error at line 384)
- **Issue:** Multi-replace tool applied extra indentation to `try` block body, causing missing `except` clause
- **Fix:** Re-applied correct indentation including `except ValueError` clause
- **Files modified:** `app/events/nlp.py`
- **Commit:** eede3ae

---

## Self-Check: PASSED

- SUMMARY.md: present (this file)
- Commit 2dd0707 (RED tests): present
- Commit eede3ae (GREEN implementation): present
- All 18 tests in test_calendar_views.py pass
