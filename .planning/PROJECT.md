# CalendarPlanner

## What This Is

A shared household calendar web application that lets two people (e.g., partners/spouses) collaboratively manage their schedule from a single source of truth. It supports recurring and one-time events, push sync to Google Calendar, natural-language event requests, image-based event extraction, and full Polish/English localization — keeping both users aligned on the family schedule across all devices.

## Core Value

A shared calendar both partners can edit that stays in sync with Google Calendar, so the family schedule is always current everywhere — on the web and on their phones.

## Current State

- v2.1 shipped on 2026-03-21.
- Event privacy: visibility toggle, lock icons, partner filtering, sync retraction to Google Calendar.
- Reminder UI: chip-based multi-reminder form with toggle, add/remove (up to 5), edit prefill, GCal sync.
- Multi-year budget: year navigation with carry-forward balance, manual override, year bounds.
- Year-over-year comparison: side-by-side annual totals with color-coded delta arrows.
- Historical import: TSV paste for past-year income hours/rates, one-time & recurring expenses.
- Full household budget tracker: income calculation from 3 hourly rates, expense management, 12-month year overview with running balance.
- Full Polish/English localization with language switcher, persisted preference, and locale-aware NLP/OCR parsing.
- Budget stats dashboard with yearly summary cards, monthly bar chart, best/worst months, and YoY comparison.
- 270 tests passing across auth, events, calendar, NLP, sync, budget, and performance.
- ~8,137 LOC Python (app + tests), plus HTML templates, CSS, and JSON locale files.
- Planning artifacts for v1.0, v1.1, v2.0, v2.1 archived under `.planning/milestones/`.

## Requirements

### Validated

- ✓ Two users can share a single calendar and each add/edit events — v1.0
- ✓ Events can be recurring (daily/weekly/monthly/yearly) — v1.0
- ✓ View upcoming events for the current day and month — v1.0
- ✓ Export/sync events to Google Calendar for both linked users — v1.0
- ✓ Natural-language request processing with review-before-save flow — v1.0
- ✓ Image input extraction with confidence/review and fallback — v1.0
- ✓ Modal-first event entry UX with keyboard and mobile support — v1.0
- ✓ Polish as default locale across all user-facing views and messages — v1.1
- ✓ Language switcher (Polish/English) with persistent preference — v1.1
- ✓ Bilingual copy coverage for auth, calendar, events, sync, NLP, and OCR — v1.1
- ✓ Locale-aware date/time formatting in Polish and English — v1.1
- ✓ NLP and OCR parsing with Polish phrases and diacritics — v1.1
- ✓ Day-click quick-entry for rapid event creation (auto end-time +1h) — v1.1
- ✓ Google Calendar reminder payload support (backend/sync) — v1.1
- ✓ Budget settings with 3 hourly rates, flat ZUS/accounting costs, initial balance — v2.0
- ✓ Income calculation engine with gross/net per month, additional household earnings — v2.0
- ✓ Recurring and one-time expense management with CRUD — v2.0
- ✓ 12-month year overview with running account balance — v2.0
- ✓ Budget localization (Polish required, English via existing i18n) — v2.0
- ✓ Accordion month detail with inline one-time expense CRUD — v2.0
- ✓ Prebuilt Tailwind CSS replacing CDN dependency (34KB vs ~300KB) — v2.0
- ✓ httpx connection pooling in SupabaseStore — v2.0
- ✓ Cache-Control headers on static assets (7-day cache) — v2.0

- ✓ Event visibility toggle — private events hidden from partner entirely — v2.1
- ✓ Reminder UI in event forms — toggle with editable defaults, chip-based add/remove, GCal sync — v2.1
- ✓ Multi-year budget browsing — year navigation with carry-forward balance — v2.1
- ✓ Year-over-year summary comparison — income, expenses, balance totals side-by-side — v2.1
- ✓ Historical year import — TSV paste for past-year data (income hours, expenses) — v2.1

### Active

**Current Milestone: v3.0 — Dashboard, Notifications & Categories**

**Goal:** Add a unified dashboard home page, partner notifications (in-app + email), event categories with color coding, expense categories with budget limits and charts, and a shared shopping list.

**Target features:**
- Dashboard home page — today's events, next 7 days preview, current month budget snapshot, quick-add
- Notifications — in-app activity feed + optional email alerts for partner event changes
- Event categories & colors — preset categories (Work, Personal, Health, Errands, Social) + custom, color-coded on calendar grid
- Expense categories — tag expenses, filter/group, pie/bar chart breakdown, per-category budget limits with alerts
- Shared shopping list — add/delete items, accepts string input to parse, both users share the list

### Out of Scope additions from v2.0/v3.0

- Budget-to-calendar event integration — independent features

### Out of Scope

- More than two concurrent users / team calendars — focus on household pair first
- Native mobile app — Google Calendar on phone handles mobile access via sync
- Full two-way Google Calendar sync as v1 — export/push covers the core need

- Two-way sync between budget and calendar events

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
| Polish as default locale | Target user base is Polish-speaking household | ✓ Implemented |
| Cookie + query param locale cascade | Simple, stateless persistence without DB migration | ✓ Implemented |
| Bilingual keyword fallback in NLP | Users may mix Polish and English; always check both | ✓ Implemented |
| Day-click quick-entry vs full form | Parallel entry modes for speed vs control | ✓ Implemented |
| Backend-only reminder support | Ship reminder sync now, UI later when needed | ✓ Implemented |

| Budget Tracker as new feature module | New user need: household financial planning alongside calendar | ✓ Shipped v2.0 |
| Current year only for budget | Simplest scope; future years deferred | ✓ v2.0 decision |
| Polish required, English optional (i18n) | Follow existing i18n if low effort; Polish-only acceptable | ✓ v2.0 decision |
| Flat ZUS + accounting costs | Same every month, configured once in settings | ✓ v2.0 decision |
| Accordion month detail for overview | Users need one-time expense breakdown per month | ✓ Shipped v2.0 |
| Prebuilt CSS over CDN | Eliminate runtime dependency, reduce payload 10x | ✓ Shipped v2.0 |
| Singleton httpx client | Reduce connection overhead across requests | ✓ Shipped v2.0 |
| Cache-Control on static assets | Faster repeat page loads | ✓ Shipped v2.0 |
| Lock emoji as sole privacy indicator | Simple, no background color change needed | ✓ Shipped v2.1 |
| Chip-based reminder UI with max 5 | Intuitive add/remove UX, reasonable limit | ✓ Shipped v2.1 |
| Carry-forward balance computation | Prior year ending balance → next year starting balance | ✓ Shipped v2.1 |
| Unicode arrows for YoY deltas | No icon library dependency | ✓ Shipped v2.1 |
| TSV paste for historical import | Simple, no file upload needed | ✓ Shipped v2.1 |

---
*Last updated: 2026-03-22 after v3.0 milestone started*
