---
phase: 28-licensing
plan: 02
subsystem: legal
tags: [agpl, license, readme, pyproject]

requires:
  - phase: 28-licensing
    provides: COMMERCIAL-LICENSE.md and MONETIZATION.md from plan 01
provides:
  - Verified LICENSE with correct AGPL-3.0 copyright
  - pyproject.toml license classifier (AGPL-3.0-or-later)
  - README.md Licensing section linking LICENSE, COMMERCIAL-LICENSE.md, MONETIZATION.md
affects: []

tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - pyproject.toml
    - README.md

key-decisions:
  - "Updated existing License section rather than adding a duplicate"
  - "Added AGPL-3.0-or-later license field to pyproject.toml"

patterns-established: []

requirements-completed:
  - MON-01
  - MON-03

duration: 3min
completed: 2026-03-23
---

# Plan 28-02: LICENSE Verification and README Licensing Section

**README now links to all licensing documents — AGPL-3.0 verified, pyproject.toml classified.**

## Performance

- **Duration:** 3 min
- **Tasks:** 2/2 completed
- **Files modified:** 2

## Accomplishments
- Verified LICENSE file correctness (AGPL-3.0, Copyright (C) 2026 Wojciech)
- Added `license = {text = "AGPL-3.0-or-later"}` to pyproject.toml
- Updated README.md License section with AGPL-3.0 summary and links to COMMERCIAL-LICENSE.md and MONETIZATION.md

## Task Commits

1. **Task 1: Verify and update LICENSE file** — `112e57b` (feat)
2. **Task 2: Add Licensing section to README.md** — `e2f5795` (feat)

## Files Created/Modified
- `pyproject.toml` — Added AGPL-3.0-or-later license classifier
- `README.md` — Updated License section with dual-license links and AGPL summary

## Decisions Made
- Updated existing `## License` section (was a single line) instead of adding a new section
- LICENSE file already correct — no modification needed

## Deviations from Plan
None — plan executed exactly as written.

## Issues Encountered
None. Pre-existing test failure in `test_calendar_views.py::test_day_view_renders_category_color_indicator` — unrelated to phase 28 (documentation-only phase).
