---
phase: 05-natural-language-input
plan: 04
subsystem: events-nlp
tags: [nlp, parsing, timezone, regression]
requires: [05-03]
provides: [NLP-01]
affects: [api/events/parse, nlp/parser]
tech_stack:
  added: []
  patterns: [tdd, regression-tests, timezone-propagation]
key_files:
  created: []
  modified:
    - app/events/nlp.py
    - app/events/routes.py
    - tests/test_nlp.py
    - tests/test_events_api.py
decisions:
  - "Allow recurrence-only phrases to anchor start_at to context date with default time when no explicit date anchor is provided"
  - "Resolve parse timezone from user/calendar context and fallback to UTC when unavailable"
metrics:
  duration_minutes: 37
  completed_at: 2026-03-19T12:10:00Z
  tasks_completed: 2
  files_touched: 4
---

# Phase 05 Plan 04: NLP Parser Reliability Fixes Summary

Implemented parser and endpoint reliability fixes so core Phase 05 natural-language flows parse correctly and respect user timezone context.

## Tasks Completed

| Task | Status | Commit | Notes |
| --- | --- | --- | --- |
| 1 | Completed | bf6ef00 | Added failing regression tests for plain weekday parsing, in-3-days hour semantics, and parse timezone propagation. |
| 2 | Completed | 77baf0c | Implemented parser and route changes to satisfy regressions and stabilize related NLP behaviors. |

## Verification

- `.venv\Scripts\python.exe -m pytest -q tests/test_nlp.py tests/test_events_api.py -k "dentist or in_3_days or parse"` (RED expected, before implementation)
- `.venv\Scripts\python.exe -m pytest -q tests/test_nlp.py tests/test_events_api.py` (GREEN, 34 passed)
- `.venv\Scripts\python.exe -c "from datetime import datetime; from app.events.nlp import NLPService; r=NLPService().parse('dentist Thursday 2pm','UTC',datetime(2026,3,19,0,0,0)); print(r.title, r.start_at.isoformat() if r.start_at else None, r.errors)"` (smoke check passed)

## Deviations from Plan

### Auto-fixed Issues

1. [Rule 1 - Bug] Fixed title extraction and explicit-date past-date regression behavior discovered during Task 1 RED run.
- Found during: Task 1 verification
- Issue: Existing parser produced malformed titles from date tokens and masked explicit past-date errors.
- Fix: Normalized title cleaning and propagated explicit parse errors through date parsing pipeline.
- Files modified: app/events/nlp.py
- Commit: 77baf0c

2. [Rule 3 - Blocking Issue] Added recurrence-only phrase anchoring to unblock full required test suite verification.
- Found during: Task 2 verification
- Issue: Full plan verification command failed on recurrence phrases without explicit date anchors.
- Fix: Allowed recurrence-only phrases to default start_at from context date/time and improved interval recurrence detection.
- Files modified: app/events/nlp.py
- Commit: 77baf0c

## Auth Gates

None.

## Self-Check: PASSED

- FOUND: .planning/phases/05-natural-language-input/05-04-SUMMARY.md
- FOUND: bf6ef00
- FOUND: 77baf0c
