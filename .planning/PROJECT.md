# CalendarPlanner

## What This Is

A shared household calendar and finance web application that lets two people (e.g., partners/spouses) collaboratively manage their schedule, budget, and shopping from a single source of truth. It supports recurring and one-time events with category color coding, push sync to Google Calendar, natural-language event requests, image-based event extraction, a full household budget tracker with expense categorization and charts, a shared shopping list with store-section auto-grouping, partner activity notifications, and a unified dashboard — all with Polish/English localization.

## Core Value

A shared calendar both partners can edit that stays in sync with Google Calendar, so the family schedule is always current everywhere — on the web and on their phones.

## Current State

- v3.0 shipped on 2026-03-23.
- Dashboard home page: today's events, 7-day preview, budget snapshot, quick-add buttons.
- In-app notifications: bell icon with unread badge, partner change alerts, SMTP email toggle, event reminders.
- Event categories & colors: preset + custom categories, curated palette, color-coded calendar grid, category filtering.
- Expense categories & charts: categorization, CSS-only pie/bar charts, smart keyword auto-detection.
- Shared shopping list: Biedronka store-section auto-grouping, multi-item paste, keyword learning.
- Event privacy: visibility toggle, lock icons, partner filtering, sync retraction to Google Calendar.
- Reminder UI: chip-based multi-reminder form with toggle, add/remove (up to 5), edit prefill, GCal sync.
- Multi-year budget: year navigation with carry-forward balance, manual override, year bounds.
- Full household budget tracker: income calculation from 3 hourly rates, expense management, 12-month year overview.
- Full Polish/English localization with language switcher, persisted preference, and locale-aware NLP/OCR parsing.
- 331 tests passing across auth, events, calendar, NLP, sync, budget, shopping, dashboard, and performance.
- ~10,686 LOC Python (6,106 app + 4,580 tests), plus HTML templates, CSS, and JSON locale files.
- Planning artifacts for v1.0, v1.1, v2.0, v2.1, v3.0 archived under `.planning/milestones/`.

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

- ✓ Event categories with preset + custom, curated palette colors — v3.0
- ✓ Color-coded calendar grid indicators and category filtering — v3.0
- ✓ Expense categories with preset + custom, pie/bar chart spending breakdown — v3.0
- ✓ Expense category auto-detection from keywords — v3.0
- ✓ Shared shopping list with Biedronka store-section auto-grouping — v3.0
- ✓ Multi-item paste for shopping list (comma/newline separated) — v3.0
- ✓ In-app notification feed with bell icon and unread badge — v3.0
- ✓ Partner change notifications for events, expenses, and income — v3.0
- ✓ Optional SMTP email alerts for partner activity — v3.0
- ✓ Event reminder notifications at configured times — v3.0
- ✓ Dashboard home page with today's events, 7-day preview, budget snapshot — v3.0
- ✓ Quick-add buttons on dashboard for events and expenses — v3.0

### Active

*(No active milestone — start next with `/gsd-new-milestone`)*

**Candidates for next milestone:**
- Per-category budget limits with 80%/100% spending alerts (BLIM-01, BLIM-02)
- Shopping list check-off/uncheck (SHOP-03)
- Shopping list change notifications (NOTIF-09)
- Daily digest email (NOTIF-10)
- Notification preference granularity (NOTIF-11)

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
| Lazy-seeded categories | Preset categories created on first GET — no migration seeding | ✓ Shipped v3.0 |
| CSS-only conic-gradient charts | No chart library dependency — pure CSS donut + bars | ✓ Shipped v3.0 |
| Keyword-based category auto-detection | Pattern matching from JSON keywords instead of ML | ✓ Shipped v3.0 |
| Biedronka store-section layout | Optimized for user's actual supermarket for route shopping | ✓ Shipped v3.0 |
| Notification hooks in routes (not services) | Matches GoogleSync pattern, try/except wrapping | ✓ Shipped v3.0 |
| HTMX polling for notification badge | 30s poll interval — simple, no WebSocket needed | ✓ Shipped v3.0 |
| Dashboard as home page (/ → /dashboard) | Most useful landing page; calendar moved to /calendar | ✓ Shipped v3.0 |

---
*Last updated: 2026-03-23 after v3.0 milestone completed*
