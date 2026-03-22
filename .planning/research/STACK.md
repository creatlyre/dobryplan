# Stack Research

**Domain:** Household calendar + budget app — v3.0 additions
**Researched:** 2026-03-22
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

No changes to core stack. Python/FastAPI, Supabase (PostgreSQL), Jinja2 templates, Tailwind CSS (prebuilt), and httpx all remain as-is.

### New Dependencies

| Technology | Version | Purpose | Why Recommended |
|---|---|---|---|
| **Chart.js** | 4.5.1 | Pie/bar charts for expense category breakdown | De facto standard JS charting library. 3.4M weekly npm downloads. Loaded via CDN `<script>` tag — zero build step, consistent with existing Google Fonts CDN usage. Built-in pie, doughnut, bar chart types with tooltips, legends, and responsive sizing. ~67KB gzipped via CDN. The existing budget_stats page uses CSS-width bars which can't do pie charts. |
| **aiosmtplib** | 5.1.0 | Async email sending for partner notifications | Native asyncio SMTP client — works directly with FastAPI's async handlers and `BackgroundTasks`. Zero dependencies. Python's built-in `email.message.EmailMessage` for message construction + Jinja2 (already in stack) for HTML email templates. Released Jan 2026, requires Python 3.10+. |

### Supporting Libraries (already in stack, newly leveraged)

| Library | Version | New Usage | Integration Point |
|---|---|---|---|
| **FastAPI BackgroundTasks** | built-in | Fire-and-forget email dispatch after event mutations | Add `background_tasks: BackgroundTasks` param to event endpoints. Sends email without blocking HTTP response. No Celery/Redis needed for 2-user volume. |
| **Jinja2** | 3.1.2 (existing) | HTML email templates | Render notification emails using same Jinja2 engine as page templates. Create `app/templates/emails/` directory. |
| **httpx** | 0.25.2 (existing) | Supabase queries for new tables (notifications, categories, shopping_list) | Same `SupabaseStore` pattern for all new CRUD operations. |

### Frontend (no build step)

| Technology | Version | Purpose | Integration |
|---|---|---|---|
| **Chart.js via CDN** | 4.5.1 | Category pie chart + monthly category bar chart | Single `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js">` in templates that need charts. Canvas element + ~20 lines JS per chart. |
| **CSS custom properties** | native | Event category color coding on calendar grid | Define `--cat-work`, `--cat-personal`, etc. in style.css. Apply via `style` attribute from category color stored in DB. No library needed. |

### Development Tools

| Tool | Purpose | Notes |
|---|---|---|
| **Supabase migrations** | Schema changes for new tables | Continue existing pattern in `supabase/migrations/`. New tables: `event_categories`, `expense_categories`, `notifications`, `shopping_list_items`. |
| **pytest** | Tests for new features | Continue existing 270-test suite. Add tests for notification service, category CRUD, shopping list, dashboard aggregation. |

## Installation

```bash
# Single new Python dependency
pip install aiosmtplib==5.1.0

# Chart.js is loaded via CDN in HTML templates — no pip/npm install needed
# Add to templates: <script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js"></script>
```

Add to `requirements.txt`:
```
aiosmtplib==5.1.0
```

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|---|---|---|---|
| **Charts** | Chart.js 4.5.1 (CDN) | Pure CSS/SVG bars (current approach) | Current CSS-width bars can't render pie charts. Chart.js adds tooltips, legends, responsive sizing with minimal code. |
| **Charts** | Chart.js 4.5.1 (CDN) | Apache ECharts | Heavier (~800KB), overkill for 2 chart types. Chart.js is ~67KB gzipped and covers pie + bar. |
| **Charts** | Chart.js 4.5.1 (CDN) | D3.js | Low-level. Requires significant code for basic pie/bar charts. Chart.js is declarative config. |
| **Email** | aiosmtplib 5.1.0 | fastapi-mail | Wrapper around aiosmtplib + Jinja2. We already have Jinja2 — fastapi-mail adds unnecessary abstraction layer. |
| **Email** | aiosmtplib 5.1.0 | Resend / SendGrid API | External SaaS dependency + API key management for a 2-user household app. SMTP against any provider (Gmail, Outlook) is simpler and free. |
| **Task queue** | FastAPI BackgroundTasks | Celery + Redis | Massive overkill. Max 2 users = max ~10 emails/day. BackgroundTasks handles this trivially. |
| **Real-time** | Polling (fetch every 60s) | WebSockets | 2-user household app doesn't need sub-second updates. Polling every 60s for the notification badge is simple and sufficient. Avoids WebSocket connection management complexity. |
| **Notification push** | In-app feed (DB query) | Web Push API / Service Workers | Adds significant complexity (VAPID keys, service worker lifecycle). Users already get phone push via Google Calendar sync. In-app feed covers the "what did my partner change?" use case. |

## What NOT to Use

| Technology | Why Avoid |
|---|---|
| **WebSocket library (websockets, socket.io)** | 2 users don't need real-time push. Polling every 60s for notification badge is simpler, stateless, and works with existing httpx/Supabase architecture. |
| **Celery / Redis / RQ** | Task queue is overkill for sending <10 emails/day. FastAPI `BackgroundTasks` handles this in-process without infrastructure. |
| **React / Vue / HTMX** | App is server-rendered Jinja2 + vanilla JS. Adding a frontend framework for charts and a notification dropdown would fragment the codebase. Chart.js works with vanilla JS + canvas. |
| **Chart.js via npm + bundler** | The app has no JS build step (no webpack/vite/esbuild). CDN script tag is consistent with existing approach (Google Fonts CDN, prebuilt Tailwind CSS). |
| **fastapi-mail** | Wraps aiosmtplib + Jinja2 with config classes. Since we already use Jinja2 for page templates, calling `aiosmtplib.send()` directly is cleaner and has fewer moving parts. |
| **SQLAlchemy / ORM** | App uses Supabase REST API via httpx. No ORM layer exists. Don't introduce one for new tables — continue the `SupabaseStore` + dataclass pattern. |
| **Separate notification microservice** | 2-user scope. In-process notification with BackgroundTasks is the right scale. |

## Integration Points

### Chart.js ↔ Existing Templates
- Add `<script>` tag to `base.html` `{% block scripts %}` or only on pages that need it (expense stats, dashboard).
- Charts consume JSON data from existing `/api/budget/` endpoints (extended with category grouping).
- Follows same pattern as budget_stats.html: JS fetches API → renders into DOM. Replace CSS-width bars with Chart.js bar chart if desired, or keep both.

### aiosmtplib ↔ FastAPI
- New `app/notifications/email_service.py` with async `send_notification_email()`.
- Called via `BackgroundTasks.add_task()` in event/expense mutation endpoints.
- SMTP config added to `config.py` Settings: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `NOTIFICATIONS_ENABLED`.
- Email templates in `app/templates/emails/` rendered with existing Jinja2 engine.

### In-App Notifications ↔ Supabase
- New `notifications` table: `id`, `calendar_id`, `user_id` (recipient), `actor_user_id`, `type` (event_created, event_updated, etc.), `payload` (JSON), `read`, `created_at`.
- New `app/notifications/` module following existing pattern: `repository.py`, `service.py`, `routes.py`, `schemas.py`.
- Frontend: polling endpoint `GET /api/notifications?unread=true` every 60s. Badge count in navbar. Dropdown list.

### Event Categories ↔ Calendar Grid
- New `event_categories` table: `id`, `calendar_id`, `name`, `color` (hex), `icon` (optional emoji), `is_default`, `sort_order`.
- Events gain `category_id` FK (nullable for backward compat).
- Calendar grid template adds `style="border-left: 3px solid {{ event.category_color }}"` or similar color indicator.
- Preset categories seeded on calendar creation: Work, Personal, Health, Errands, Social.

### Expense Categories ↔ Budget Module
- New `expense_categories` table: `id`, `calendar_id`, `name`, `color` (hex), `budget_limit` (nullable), `sort_order`.
- Expenses gain `category_id` FK (nullable for backward compat).
- New API endpoints: `GET /api/budget/expenses/by-category?year=2026` returns grouped totals.
- Chart.js pie chart consumes this grouped data. Budget limit alerts shown when category spend exceeds limit.

### Shopping List ↔ Existing CRUD Pattern
- New `shopping_list_items` table: `id`, `calendar_id`, `name`, `checked`, `added_by_user_id`, `created_at`.
- Follows same Supabase REST pattern as events/expenses.
- String-input parsing: split on commas/newlines, trim, create multiple items. Pure Python, no library.

### Dashboard ↔ Existing Services
- New `app/dashboard/` module with `service.py` and `routes.py`.
- Aggregates data from existing services: `EventService` (today's + next 7 days), `OverviewService` (current month budget snapshot).
- Single `/` route replaces current calendar-only home page, or new `/dashboard` route.

### Config Additions (config.py)
```python
# Email / SMTP
SMTP_HOST: str = ""
SMTP_PORT: int = 587
SMTP_USERNAME: str = ""
SMTP_PASSWORD: str = ""
SMTP_FROM_EMAIL: str = ""
SMTP_USE_TLS: bool = True
NOTIFICATIONS_ENABLED: bool = False  # Off by default, opt-in
```

## New DB Tables Summary

| Table | Purpose | Key Columns |
|---|---|---|
| `event_categories` | Category presets + custom per calendar | `id`, `calendar_id`, `name`, `color`, `icon`, `is_default`, `sort_order` |
| `expense_categories` | Expense grouping with optional budget limits | `id`, `calendar_id`, `name`, `color`, `budget_limit`, `sort_order` |
| `notifications` | In-app activity feed | `id`, `calendar_id`, `user_id`, `actor_user_id`, `type`, `payload`, `read`, `created_at` |
| `shopping_list_items` | Shared shopping list | `id`, `calendar_id`, `name`, `checked`, `added_by_user_id`, `created_at` |

## Sources

- Chart.js 4.5.1: https://www.npmjs.com/package/chart.js (verified 2026-03-22, 3.4M weekly downloads) — HIGH confidence
- Chart.js docs: https://www.chartjs.org/docs/latest/ (v4 migration guide, pie/bar/doughnut examples via Context7)
- aiosmtplib 5.1.0: https://pypi.org/project/aiosmtplib/ (released 2026-01-25, Python 3.10+) — HIGH confidence
- aiosmtplib docs: https://aiosmtplib.readthedocs.io/en/stable/ (usage examples via Context7)
- FastAPI BackgroundTasks: https://fastapi.tiangolo.com/tutorial/background-tasks/ (verified via Context7) — HIGH confidence

