🌐 **Language / Język:** [🇬🇧 English](README.md) | [🇵🇱 Polski](README.pl.md)

# Synco

Shared household calendar, budget tracker, and shopping list for two-person households. Google sign-in, shared events with recurrence, Google Calendar sync, natural-language quick add, OCR event extraction, budget with multi-year tracking, store-section shopping lists, in-app notifications, and a dashboard home page.

## Why This Project

Synco is built for a couple or household that wants one shared source of truth for scheduling, budgeting, and grocery shopping — with reminders delivered to phones through Google Calendar.

## Current Status

- **Version:** v3.0 (shipped 2026-03-23)
- **Tests:** 331 passing across 17 test files
- **Languages:** Polish (default), English
- **Milestones shipped:**
  - v1.0 — Core calendar + Google sync
  - v1.1 — Polish localization
  - v2.0 — Budget tracker
  - v2.1 — Privacy, reminders, multi-year budget
  - v3.0 — Dashboard, notifications, categories, shopping list

## Feature Highlights

### Calendar & Events
- **Household sharing** — invite flow linking two users to one shared calendar.
- **Event CRUD** — create, edit, delete events with daily and monthly views.
- **Categories** — preset + custom event categories with curated color palette; color-coded calendar grid indicators and filter bar.
- **Recurrence** — daily, weekly, monthly, yearly via RFC 5545 RRULE patterns.
- **Privacy** — per-event visibility toggle (shared/private) with lock icons; partner filtering across all views.
- **Reminders** — up to 5 chip-based reminders per event, synced to Google Calendar.
- **Quick add (NLP)** — parse input like "dentist Thursday 2pm" into structured event data with ambiguity handling.
- **OCR quick add** — upload image, extract text, parse event fields with confidence-based review.

### Budget Tracker
- **Income** — monthly hours tracking across 3 hourly rates, flat costs, additional earnings; gross/net calculation.
- **Expenses** — full CRUD with auto-categorization via keyword dictionary; preset + custom categories; CSS-only pie/bar charts.
- **Multi-year** — year navigation with carry-forward balance, manual override, year-over-year comparison dashboard.
- **Historical import** — TSV paste for past-year income and expenses.

### Shopping List
- **Items** — add, edit, delete; multi-item paste (comma/newline separated).
- **Store sections** — Biedronka-style auto-grouping (10 sections, 150+ keywords) with emoji headers.
- **Keyword learning** — teach new item-to-section mappings; custom sections.

### Notifications
- **Partner alerts** — in-app bell icon with unread badge (HTMX 30s polling) for partner changes to events, expenses, and income.
- **Event reminders** — notification at configured reminder times.
- **Email** — optional SMTP email alerts with per-user preference toggle.

### Dashboard
- **Home page** (redirected from `/`) — today's events, 7-day preview, monthly budget snapshot (income/expenses/balance), top expense categories, quick-add buttons.

### Google Calendar Sync
- **Export** — push a month of events to Google Calendar.
- **Import** — pull events from Google Calendar with upsert and soft-delete.
- **Live hooks** — sync on create/update/delete.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.135 |
| Templating/UI | Jinja2 + server-rendered HTML + HTMX |
| Data store | Supabase (Postgres) |
| Auth | Google OAuth2 + Supabase auth + password login |
| Sync | Google Calendar API |
| Parsing | python-dateutil NLP + optional EasyOCR |
| Security | PyJWT + cryptography (token encryption) |
| Tests | pytest + pytest-asyncio + httpx |

## Repository Layout

```text
app/
  auth/           # OAuth, session, password login, token utils
  budget/         # Budget settings, income, expenses, overview, stats, import
  dashboard/      # Dashboard aggregation service and routes
  database/       # Supabase store, models, schemas
  events/         # Event CRUD, NLP, OCR, recurrence, categories
  middleware/     # Session validation middleware
  notifications/  # Partner alerts, reminders, email, preferences
  shopping/       # Shopping list items, sections, keyword learning
  sync/           # Google Calendar export/import service
  users/          # Household invitations and user profile
  views/          # HTML page routes (calendar, budget, shopping, etc.)
  templates/      # Jinja2 templates and partials
  locales/        # i18n JSON files (en.json, pl.json)

supabase/
  migrations/     # 8 Supabase migration files

tests/            # 17 test files (331 tests)
main.py           # FastAPI app entry point
config.py         # Pydantic BaseSettings, environment-driven config
```

## Prerequisites

- Python 3.10+
- pip / virtualenv
- Supabase project (URL + keys)
- Google Cloud OAuth credentials (client ID/secret)

Optional:
- `easyocr` — for OCR-based event extraction
- SMTP server — for email notifications

## Quick Start

```bash
git clone <repo-url> && cd CalendarPlanner
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn main:app --reload
```

Open:
- App: `http://localhost:8000` (redirects to dashboard)
- Health: `http://localhost:8000/health`

## Environment Variables

Create a `.env` file in the project root:

```env
# Core
DEBUG=true
SECRET_KEY=replace-with-strong-secret
DB_ENCRYPTION_KEY=replace-with-strong-encryption-key

# JWT
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=8

# Supabase
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>

# Google OAuth & Calendar
GOOGLE_CLIENT_ID=<google-client-id>
GOOGLE_CLIENT_SECRET=<google-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
GOOGLE_EVENT_REMINDER_MINUTES=30

# Email notifications (optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=<smtp-user>
SMTP_PASSWORD=<smtp-password>
SMTP_FROM_ADDRESS=noreply@example.com
SMTP_USE_TLS=true
```

Notes:
- `config.py` supports fallback names `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- OCR and email endpoints degrade gracefully when dependencies/credentials are missing.

## API Overview

### Auth
- `GET /auth/login` — initiate Google OAuth
- `GET /auth/callback` — OAuth callback
- `POST /auth/session` — set session from Supabase token
- `POST /auth/register` — password registration
- `POST /auth/password-login` — password login
- `POST /auth/logout` — clear session

### Users & Household
- `GET /api/users/me` — current user profile
- `GET /api/users/household` — household info
- `POST /api/users/invite` — send household invite
- `POST /api/users/accept-invitation` — accept invite

### Events
- `POST /api/events` — create event
- `PUT /api/events/{id}` — update event
- `DELETE /api/events/{id}` — delete event
- `GET /api/events/day` — events for a day
- `GET /api/events/month` — events for a month
- `POST /api/events/parse` — NLP parse
- `POST /api/events/ocr-parse` — OCR parse
- `GET /api/events/categories` — list categories
- `POST /api/events/categories` — create category
- `PUT /api/events/categories/{id}` — update category
- `DELETE /api/events/categories/{id}` — delete category

### Budget
- `GET/PUT /api/budget/settings` — budget settings (rates, flat costs)
- `GET /api/budget/income` — monthly income breakdown
- `PUT /api/budget/income/hours` — update hours
- `POST /api/budget/income/hours/bulk` — bulk hours
- `POST /api/budget/income/earnings` — add extra earnings
- `DELETE /api/budget/income/earnings/{id}` — remove earnings
- `GET /api/budget/expenses` — list expenses
- `POST /api/budget/expenses` — create expense
- `PUT /api/budget/expenses/{id}` — update expense
- `DELETE /api/budget/expenses/{id}` — delete expense
- `POST /api/budget/expenses/bulk` — bulk create
- `DELETE /api/budget/expenses/bulk` — bulk delete
- `GET /api/budget/expenses/by-category` — expenses by category
- `POST /api/budget/expenses/auto-categorize` — auto-categorize
- `GET /api/budget/expenses/categories` — expense categories
- `POST /api/budget/expenses/categories` — create expense category
- `PUT /api/budget/expenses/categories/{id}` — update expense category
- `DELETE /api/budget/expenses/categories/{id}` — delete expense category
- `GET /api/budget/overview` — year overview with monthly balance
- `GET /api/budget/overview/comparison` — year-over-year comparison
- `GET/POST/DELETE /api/budget/overview/carry-forward` — carry-forward overrides

### Shopping
- `GET /api/shopping/items` — list items
- `POST /api/shopping/items` — add item
- `POST /api/shopping/items/multi` — add multiple items
- `PUT /api/shopping/items/{id}` — update item
- `DELETE /api/shopping/items/{id}` — delete item
- `POST /api/shopping/items/learn` — teach keyword mapping
- `GET /api/shopping/sections` — list sections
- `POST /api/shopping/sections` — create section
- `PUT /api/shopping/sections/{id}` — update section
- `DELETE /api/shopping/sections/{id}` — delete section

### Sync
- `POST /api/sync/export-month` — push month to Google Calendar
- `POST /api/sync/import-month` — pull month from Google Calendar
- `GET /api/sync/status` — sync connection status

### Notifications
- `GET /api/notifications` — list notifications
- `GET /api/notifications/unread-count` — unread badge count
- `POST /api/notifications/{id}/read` — mark read
- `POST /api/notifications/{id}/dismiss` — dismiss
- `POST /api/notifications/read-all` — mark all read
- `GET/PUT /api/notifications/preferences` — notification preferences

### HTML Pages
- `/dashboard` — home dashboard
- `/calendar` — month calendar view
- `/calendar/month` — month event list
- `/budget/*` — budget settings, income, expenses, stats, overview, import
- `/shopping` — shopping list
- `/notifications` — notification feed
- `/invite` — household invite page

## Testing

Run all 331 tests:

```bash
pytest -q
```

Targeted suites:

```bash
pytest -q tests/test_auth.py tests/test_users.py
pytest -q tests/test_calendar_views.py tests/test_events_api.py
pytest -q tests/test_nlp.py tests/test_recurrence.py
pytest -q tests/test_expenses.py tests/test_income.py tests/test_overview.py
pytest -q tests/test_shopping.py tests/test_dashboard.py
```

## Release History

| Version | Date | Highlights |
|---------|------|-----------|
| v3.0 | 2026-03-23 | Dashboard, notifications, event/expense categories, shopping list |
| v2.1 | 2026-03-22 | Event privacy, reminders, multi-year budget, historical import |
| v2.0 | 2026-03-20 | Budget tracker (income, expenses, overview, stats) |
| v1.1 | 2026-03-20 | Polish localization, i18n framework |
| v1.0 | 2026-03-19 | Calendar CRUD, recurrence, Google sync, NLP, OCR |

Milestone archives and planning artifacts live under `.planning/`.

## Security Notes

- Do not commit real secrets — use `.env` for all credentials.
- Rotate `SECRET_KEY` and `DB_ENCRYPTION_KEY` before production.
- Use secure cookie settings and HTTPS in production.
- Tokens are encrypted at rest with Fernet (`DB_ENCRYPTION_KEY`).

## License

This project is licensed under the [GNU AGPL-3.0](LICENSE). If you host a modified version as a network service, you must publish your changes under the same license.
