# CalendarPlanner

## What This Is

A shared household calendar web application that lets two people (e.g., partners/spouses) collaboratively manage their schedule from a single source of truth. It supports recurring and one-time events, two-way sync with Google Calendar, natural-language event requests, and image-based event extraction — keeping both users aligned on the family schedule across all devices.

## Core Value

A shared calendar both partners can edit that stays in sync with Google Calendar, so the family schedule is always current everywhere — on the web and on their phones.

## Current State

- v1.0 shipped on 2026-03-19.
- Core household workflow is complete: OAuth sign-in, two-user sharing, event CRUD, recurring events, Google sync export/push, NLP quick-add, OCR quick-add, and UI/UX polish.
- Planning artifacts for v1.0 are archived under `.planning/milestones/`.

## Next Milestone Goals

- Define v1.1 scope with clear requirements and roadmap.
- Implement event visibility controls (solo/private vs shared family events) starting with Phase 8.
- Improve release hygiene by running a final milestone audit after the last completed phase before archival.

## Requirements

### Validated

- ✓ Two users can share a single calendar and each add/edit events — v1.0
- ✓ Events can be recurring (daily/weekly/monthly/yearly) — v1.0
- ✓ View upcoming events for the current day and month — v1.0
- ✓ Export/sync events to Google Calendar for both linked users — v1.0
- ✓ Natural-language request processing with review-before-save flow — v1.0
- ✓ Image input extraction with confidence/review and fallback — v1.0
- ✓ Modal-first event entry UX with keyboard and mobile support — v1.0

### Active

- [ ] Event visibility controls: solo/private events vs shared household events
- [ ] Conflict detection when both users edit the same event simultaneously
- [ ] Real-time collaboration updates between linked users
- [ ] Browser reminders with configurable reminder lead time
- [ ] Additional calendar views (weekly and multi-week agenda)

### Out of Scope

- More than two concurrent users / team calendars — focus on household pair first
- Native mobile app — Google Calendar on phone handles mobile access via sync
- Full two-way Google Calendar sync as v1 — export/push covers the core need

## Context

- Target users: two people in the same household (e.g., couple)
- Platform: Python web application
- Primary integration: Google Calendar / Google Workspace Calendar (OAuth + API)
- Event creation methods: manual UI, natural language text request, image/OCR extraction
- The user wants to see the calendar from a browser and get event reminders on their phone via Google Calendar's notification system

## Constraints

- **Tech stack**: Python — backend must be Python-based
- **Scope**: Two-user household calendar; no multi-tenancy in v1
- **Integration**: Google Calendar API (OAuth2) required for sync/export
- **User count**: Exactly two users per calendar instance for v1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python backend | User's stated tech preference | ✓ Implemented |
| Two-user model (not multi-user) | Simplest model that covers household use case | ✓ Implemented |
| Push sync to Google Calendar (not full two-way v1) | Reduces complexity; users read on phone via Google | ✓ Implemented |
| Image OCR for event extraction | Differentiating quick-add path with review safety | ✓ Implemented |

---
*Last updated: 2026-03-19 after v1.0 milestone completion*
