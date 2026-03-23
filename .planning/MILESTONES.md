# Milestones

## v3.0 Dashboard, Notifications & Categories (Shipped: 2026-03-23)

**Phases completed:** 5 phases (23-27), 11 plans

**Key accomplishments:**

- Event categories & colors: preset + custom categories with curated palette, color-coded calendar grid indicators, category filtering
- Expense categories & charts: expense categorization, CSS-only pie/bar charts on stats page, smart keyword auto-detection
- Shared shopping list: Biedronka store-section auto-grouping, multi-item paste, keyword learning, section picker UI
- In-app notifications: bell icon with unread badge, partner change alerts for events/expenses/income, SMTP email toggle, event reminder notifications
- Dashboard home page: today's events, 7-day preview, budget snapshot with monthly balance, quick-add buttons, responsive 2-column grid
- 331 tests passing across all subsystems

**Stats:**

- 164 files changed, 9,992 insertions, 12,336 deletions
- Timeline: 2026-03-22 → 2026-03-23 (2 days)
- 60 commits

**Git range:** v2.1 → v3.0

**Known tech debt:** (from milestone audit)
- No VERIFICATION.md for any v3.0 phase
- Missing SUMMARY frontmatter in phases 25, 27
- Bulk endpoints skip notification hooks (by design — prevent spam on import)

---

## v2.1 Privacy, Reminders & Multi-Year Budget (Shipped: 2026-03-22)

**Phases completed:** 5 phases (18-22), 7 plans

**Key accomplishments:**

- Event privacy: visibility toggle in event forms, lock icon for private events, partner filtering across all views, sync retraction to Google Calendar
- Reminder UI: chip-based multi-reminder form with toggle, add/remove (up to 5), edit prefill, synced to Google Calendar
- Multi-year budget: year navigation with carry-forward balance computation, year bounds detection, manual carry-forward override
- Year-over-year comparison: side-by-side annual totals (income, expenses, balance) with color-coded delta arrows
- Historical year import: TSV paste interface for past-year income hours/rates, one-time & recurring expenses
- 270 tests passing across all subsystems

**Stats:**

- 45 files changed, 4,053 insertions, 104 deletions
- Timeline: 2026-03-20 → 2026-03-21 (2 days)
- 34 commits

**Git range:** v2.0 → v2.1

---

## v2.0 Budget Tracker (Shipped: 2026-03-20)

**Phases completed:** 6 phases (12-17), 14 plans

**Key accomplishments:**

- Budget settings with 3 hourly rates, ZUS/accounting costs, and initial bank balance
- Income calculation engine with gross/net per month, additional household earnings
- Recurring and one-time expense management with CRUD
- 12-month year overview with running account balance
- Accordion month detail — click any month to expand inline one-time expense CRUD
- Prebuilt Tailwind CSS (34KB) replacing CDN runtime dependency (~300KB)
- httpx connection pooling and Cache-Control headers on static assets
- 230 tests passing across all subsystems

**Stats:**

- 23 files changed (Phases 16-17 alone: 1,627 insertions, 321 deletions)
- Timeline: 2026-03-20 (1 day)
- 12 commits

**Git range:** v1.1 -> v2.0

---

## v1.1 Localization and Language Switching (Shipped: 2026-03-20)

**Phases completed:** 4 phases, 10 plans, 0 tasks

**Key accomplishments:**

- Built i18n foundation with `resolve_locale()`, `translate()`, and Jinja template integration — Polish as default locale across all views.
- Added language switcher UI (Polish/English) with cookie and localStorage persistence.
- Enabled locale-aware NLP and OCR parsing with Polish keyword dictionaries and bilingual fallback.
- Implemented day-click quick-entry for rapid event creation with auto-calculated end-time (+1h).
- Added multi-reminder support to Event model with Google Calendar sync payload generation.
- Comprehensive test coverage: 145 tests passing across auth, events, views, NLP, sync, and integration.

**Stats:**

- 60 files changed
- 5,014 insertions, 479 deletions
- Timeline: 2026-03-19 to 2026-03-20 (2 days)
- 47 commits

**Git range:** ebe4787 -> 4026efa

**Known gaps:**

- Phases 08, 09, 10 missing formal VERIFICATION.md files (process gaps only — all tests green)
- Phase 9 SUMMARY frontmatter `requirements_completed` empty (should list I18N-02, I18N-03, I18N-06)
- Reminder UI not exposed in quick-entry form (backend supports it, deferred to v2 REM-02)

---

## v1.0 milestone (Shipped: 2026-03-19)

**Delivered:** Household shared-calendar MVP with Google auth, event CRUD/recurrence, Google sync, NLP/OCR quick-add, and final UI/UX polish.

**Phases completed:** 7 phases, 22 plans, 39 tasks

**Key accomplishments:**

- Implemented two-user household invitation and shared calendar access flow.
- Delivered authenticated event CRUD with month/day calendar views and interactive UI updates.
- Added RFC5545 recurrence support with DST-safe handling.
- Added Google Calendar export and automatic sync hooks for event create/update/delete.
- Added quick-add natural language parsing, ambiguity-year confirmation, and OCR image extraction with review/fallback.
- Completed UI/UX hardening: invite back navigation, modal entry workflow, keyboard/focus behavior, and mobile responsiveness with regression coverage.

**Stats:**

- 129 files changed
- 17,380 insertions, 2 deletions
- Timeline: 2026-03-18 to 2026-03-19

**Git range:** 3e8eed6bfb14cef7a352b93ba4d70f62b907e235 -> 2368f2d0c519236484961f9c6e74769289c58ba4

**Known gaps:**

- Milestone audit is present and passed for phases 1-6; phase 7 was completed afterward without a separate final audit pass.

---
