# Architecture Research

**Domain:** Household calendar + budget app — v3.0 integration
**Researched:** 2026-03-22
**Confidence:** HIGH

## System Overview

```
                          ┌──────────────────────────────────────────────┐
                          │              FastAPI Application             │
                          │  main.py — mounts routers, middleware        │
                          └──────────────┬─────────────────────────────┬─┘
                                         │                             │
         ┌───────────────────────────────┼─────────────────────────────┼───────────────────────┐
         │ Router Layer (routes.py / views.py per module)              │                       │
         │                                                            │                       │
  EXISTING MODULES                                    NEW MODULES (v3.0)                      │
  ┌──────────────┐  ┌──────────────┐            ┌───────────────┐  ┌──────────────┐           │
  │  app/auth/   │  │ app/events/  │            │ app/dashboard/ │  │app/notifica- │           │
  │  routes.py   │  │  routes.py   │            │  routes.py     │  │  tions/      │           │
  │  supabase_   │  │  service.py  │◄──MODIFY──►│  service.py    │  │  routes.py   │           │
  │  auth.py     │  │  repository  │ add categ  │  (aggregator)  │  │  service.py  │           │
  └──────────────┘  │  schemas.py  │ fields     └───────────────┘  │  repository  │           │
                    │  nlp.py      │                                │  email.py    │           │
  ┌──────────────┐  │  ocr.py      │            ┌───────────────┐  └──────────────┘           │
  │  app/budget/ │  └──────────────┘            │ app/shopping/  │                            │
  │  expense_*   │◄──MODIFY: add                │  routes.py     │  ┌──────────────┐          │
  │  income_*    │   category fields            │  service.py    │  │ app/categories│          │
  │  overview_*  │                              │  repository.py │  │  routes.py    │          │
  │  views.py    │                              │  schemas.py    │  │  service.py   │          │
  └──────────────┘                              └───────────────┘  │  repository   │          │
                                                                   └──────────────┘          │
  ┌──────────────┐  ┌──────────────┐                                                         │
  │  app/sync/   │  │  app/users/  │                                                         │
  │  service.py  │  │  repository  │                                                         │
  └──────────────┘  └──────────────┘                                                         │
         │                                                                                    │
         └────────────────────────────────┬───────────────────────────────────────────────────┘
                                          │
         ┌────────────────────────────────▼────────────────────────────┐
         │ Data Layer                                                  │
         │  app/database/supabase_store.py — httpx REST to Supabase   │
         │  app/database/models.py         — @dataclass domain models │
         │  app/database/database.py       — get_db() → SupabaseStore │
         └────────────────────────────────┬────────────────────────────┘
                                          │
         ┌────────────────────────────────▼──────────────────────────┐
         │ Supabase PostgreSQL                                       │
         │  EXISTING: users, calendars, calendar_invitations,        │
         │            events, budget_settings, monthly_hours,        │
         │            additional_earnings, expenses,                  │
         │            carry_forward_overrides                         │
         │                                                           │
         │  NEW (v3.0): event_categories, expense_categories,        │
         │              notifications, shopping_items,                │
         │              expense_category_budgets, user_preferences    │
         └───────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Existing Modules (no architectural changes)

| Component | Responsibility | Pattern |
|-----------|---------------|---------|
| `app/auth/` | Cookie-based JWT auth, Supabase auth, Google OAuth | dependencies.py exports `get_current_user` |
| `app/events/` | Event CRUD, NLP parsing, OCR, recurrence expansion | repository → service → routes |
| `app/budget/` | Income, expenses, overview, settings, stats | `*_repository.py`, `*_service.py`, `*_routes.py`, `*_views.py` |
| `app/sync/` | Google Calendar push sync | service.py orchestrates per-user GCal API |
| `app/users/` | User/calendar/invitation CRUD | repository → service → routes |
| `app/views/` | Calendar HTML page routes (Jinja2) | calendar_routes.py returns template responses |
| `app/database/` | SupabaseStore (httpx REST), dataclass models, get_db() | Singleton httpx client, PostgREST API |
| `app/i18n.py` | Locale resolution, translation, template injection | `inject_template_i18n()`, JSON locale files |

### New Modules (v3.0)

| Component | Responsibility | Pattern |
|-----------|---------------|---------|
| `app/dashboard/` | Aggregator: today's events, 7-day preview, budget snapshot, notifications | service.py calls into events + budget + notifications services |
| `app/notifications/` | In-app notification feed + email dispatch | repository → service → routes; `email.py` for SMTP/Resend |
| `app/categories/` | Shared category definitions for events & expenses | repository → service → routes |
| `app/shopping/` | Shared shopping list CRUD + text parsing | repository → service → routes |

## New Modules — Detailed Structure

### 1. `app/categories/` — Category Management

Shared categorical system used by both events and expenses.

```
app/categories/
├── __init__.py
├── models.py          # EventCategory, ExpenseCategory dataclasses
├── repository.py      # CategoryRepository (CRUD for both types)
├── schemas.py         # Pydantic: CategoryCreate, CategoryUpdate, CategoryResponse
├── service.py         # CategoryService — validation, defaults seeding
└── routes.py          # API: /api/categories/events, /api/categories/expenses
```

**Why a shared module:** Both event and expense categories are scoped to `calendar_id`, share color/icon semantics, and need CRUD. Separate modules would duplicate 80% of the logic. However, they use **separate tables** (`event_categories`, `expense_categories`) because their extra fields differ (expenses have `budget_limit`, events don't).

**Preset seeding:** On first access per calendar, seed default event categories (Work, Personal, Health, Errands, Social) and default expense categories (Housing, Food, Transport, Utilities, Entertainment, Health, Other). The service checks if categories exist for that calendar before seeding.

### 2. `app/notifications/` — In-App Feed + Email Alerts

```
app/notifications/
├── __init__.py
├── models.py          # Notification dataclass
├── repository.py      # NotificationRepository — insert, list, mark-read
├── schemas.py         # NotificationCreate, NotificationResponse
├── service.py         # NotificationService — create-and-dispatch logic
├── email.py           # Email sender (Resend API or SMTP)
└── routes.py          # API: /api/notifications (GET list, POST mark-read)
```

**Notification trigger pattern:** Notifications are created as a **side-effect** in existing service methods. Rather than modifying every service, use a lightweight emitter pattern:

```python
# app/notifications/emitter.py
class NotificationEmitter:
    def __init__(self, notification_service: NotificationService):
        self.svc = notification_service

    def on_event_created(self, event: Event, actor_user_id: str, calendar_id: str):
        """Notify the other household member about a new event."""
        self.svc.create_for_partner(
            calendar_id=calendar_id,
            actor_user_id=actor_user_id,
            type="event_created",
            payload={"event_id": event.id, "title": event.title},
        )
```

This emitter is called from `EventService.create_event()` and `EventService.update_event()` after the DB write succeeds. The notification service resolves the partner user from `calendar_id` and creates the notification row + optionally sends email.

**Email dispatch:** Use an async background approach. Since the app is synchronous (httpx, not httpx.AsyncClient for DB), email is sent inline via a simple HTTP call to Resend API (or SMTP). Keep it simple — one POST request per notification. If it fails, the in-app notification still exists; email failure is logged but not retried.

**User preferences for email:** Add a `user_preferences` table (or a `notification_email_enabled` column on `users`) to let each user toggle email notifications on/off.

### 3. `app/dashboard/` — Dashboard Home Page

```
app/dashboard/
├── __init__.py
├── service.py         # DashboardService — aggregates data from other services
├── routes.py          # View: GET /dashboard (HTML), API: GET /api/dashboard (JSON)
└── views.py           # Template route returning dashboard.html
```

**Aggregator pattern:** `DashboardService` does NOT own data. It composes:
- `EventService.list_day_expanded()` → today's events
- `EventService.list_month_expanded()` → next 7 days (filter client-side or add a `list_range()` method)
- `OverviewService.get_month_data()` → current month budget snapshot
- `NotificationRepository.list_unread()` → recent notifications count/preview
- `ShoppingService.list_items()` → shopping list summary

```python
class DashboardService:
    def __init__(self, event_svc, overview_svc, notification_repo, shopping_svc):
        self.events = event_svc
        self.overview = overview_svc
        self.notifications = notification_repo
        self.shopping = shopping_svc

    def get_dashboard_data(self, calendar_id: str, user_id: str, year: int, month: int, day: int):
        return {
            "today_events": self.events.list_day_expanded(calendar_id, year, month, day, requesting_user_id=user_id),
            "budget_snapshot": self.overview.get_month_data(calendar_id, year, month),
            "unread_notifications": self.notifications.count_unread(calendar_id, user_id),
            "shopping_count": self.shopping.count_pending(calendar_id),
        }
```

**Root route change:** Currently `GET /` renders `calendar.html`. For v3.0, `GET /` should render `dashboard.html` instead. The calendar moves to `GET /calendar`. This is a one-line change in `main.py`. Add a nav link "Calendar" to the bottom nav / top nav alongside existing "Budget" link.

### 4. `app/shopping/` — Shared Shopping List

```
app/shopping/
├── __init__.py
├── models.py          # ShoppingItem dataclass
├── repository.py      # ShoppingRepository — add, list, check-off, delete
├── schemas.py         # ShoppingItemCreate, ShoppingItemResponse
├── service.py         # ShoppingService — text parsing, CRUD
└── routes.py          # API: /api/shopping (CRUD), view: /shopping (HTML)
```

**Text parsing:** Accept a multi-line or comma-separated string, split into individual items. No NLP needed — just `split()` on newlines/commas, strip whitespace, filter empty. Simple and reliable.

**Shared by design:** Shopping items are scoped to `calendar_id` (same as events, expenses). Both household members see the same list. No per-user filtering.

## Modified Modules

### `app/events/` — Add Category Support

| File | Change | Impact |
|------|--------|--------|
| `models.py` | Add `category_id: str \| None = None` and `category_color: str \| None = None` to `Event` dataclass | Low — additive field |
| `schemas.py` | Add `category_id: Optional[str] = None` to `EventCreate` and `EventUpdate` | Low — optional field |
| `repository.py` | Include `category_id` in `create()`, `update()`, and `_to_event()` mapping | Low — one field per method |
| `service.py` | Pass through `category_id`; optionally validate category exists | Low |

**Calendar grid color-coding:** The `_to_event()` mapper joins or looks up the category color. Two approaches:
1. **Denormalize:** Store `category_color` on the event row (simpler, one fewer query). Update color if category changes.
2. **Join:** Fetch categories once per month grid load, build a color map client-side.

**Recommendation:** Option 2 (join at view layer). Fetch `GET /api/categories/events?calendar_id=X` once when rendering `month_grid.html`, pass the color map into the template. This avoids denormalization drift and keeps the events table clean. The categories list is small (5–20 items) so the extra query is negligible.

### `app/budget/expense_*` — Add Category Support

| File | Change | Impact |
|------|--------|--------|
| `models.py` (database) | Add `category_id: str \| None = None` to `Expense` dataclass | Low |
| `expense_schemas.py` | Add `category_id: Optional[str] = None` to `ExpenseCreate`, `ExpenseUpdate` | Low |
| `expense_repository.py` | Include `category_id` in `create()`, `update()`, `_to_expense()` | Low |
| `expense_service.py` | Add `get_by_category()` method for chart breakdowns | Medium |

### `app/budget/overview_*` — Category Breakdown in Charts

| File | Change | Impact |
|------|--------|--------|
| `overview_service.py` | Add `get_category_breakdown(calendar_id, year)` method | Medium — new aggregation |
| `overview_routes.py` | Add `GET /api/budget/overview/categories?year=X` endpoint | Low |

### `main.py` — Register New Routers

```python
# New imports
from app.dashboard.views import router as dashboard_views_router
from app.notifications.routes import router as notifications_router
from app.categories.routes import router as categories_router
from app.shopping.routes import router as shopping_router

# Register
app.include_router(dashboard_views_router)
app.include_router(notifications_router)
app.include_router(categories_router)
app.include_router(shopping_router)
```

**Root route:** Change `GET /` from rendering `calendar.html` to rendering `dashboard.html` (or redirect to `/dashboard`).

### `app/templates/base.html` — Navigation Updates

Add to both top nav and mobile bottom nav:
- "Dashboard" (home icon) → `/dashboard` or `/`
- "Shopping" (list icon) → `/shopping`
- Notification bell icon with unread count badge (top nav only)

### `app/locales/en.json` + `pl.json` — New Translation Keys

Add keys for all new UI strings: dashboard labels, notification messages, category names, shopping list labels. Follow existing flat key convention (e.g., `dashboard.title`, `notifications.empty`, `shopping.add_item`, `categories.work`).

### `config.py` — Optional Email Config

```python
# Add to Settings class
RESEND_API_KEY: str = ""                    # or SMTP_* settings
NOTIFICATION_EMAIL_FROM: str = "noreply@synco.app"
NOTIFICATION_EMAIL_ENABLED: bool = False    # opt-in
```

## Data Flow

### Dashboard Load (`GET /` or `GET /dashboard`)

```
Browser → GET /dashboard
  → auth middleware validates cookie JWT
  → DashboardService.get_dashboard_data(calendar_id, user_id, today)
    ├── EventService.list_day_expanded(calendar_id, today)
    │     └── SupabaseStore.select("events", ...) + recurrence expansion
    ├── OverviewService.get_month_data(calendar_id, year, month)
    │     └── SupabaseStore.select("budget_settings"|"expenses"|"monthly_hours", ...)
    ├── NotificationRepository.count_unread(calendar_id, user_id)
    │     └── SupabaseStore.count("notifications", ...)
    └── ShoppingService.count_pending(calendar_id)
          └── SupabaseStore.count("shopping_items", ...)
  → Jinja2 renders dashboard.html with aggregated context
  → HTML response with HTMX partials for lazy-loading panels
```

### Notification Creation (side-effect of event mutation)

```
Browser → POST /api/events  (create event)
  → EventService.create_event(calendar_id, user_id, payload)
    └── EventRepository.create() → new Event row
  → NotificationEmitter.on_event_created(event, user_id, calendar_id)
    └── NotificationService.create_for_partner(...)
      ├── Resolve partner_user_id from calendar_id
      ├── SupabaseStore.insert("notifications", {...})
      └── IF partner.notification_email_enabled:
            email.send_notification(partner.email, message)
  → Return EventResponse to browser
```

### Shopping List Add (text parsing)

```
Browser → POST /api/shopping  { "text": "mleko, chleb, masło" }
  → ShoppingService.parse_and_add(calendar_id, user_id, text)
    ├── Split text by commas/newlines → ["mleko", "chleb", "masło"]
    └── For each item: ShoppingRepository.create(calendar_id, name=item)
  → Return list of ShoppingItemResponse
```

### Category-Colored Calendar Grid

```
Browser → GET /calendar/month?year=2026&month=3
  → CalendarRoutes.month_grid()
    ├── EventService.list_month_expanded(calendar_id, year, month)
    └── CategoryRepository.list_event_categories(calendar_id)
  → Template receives events + category_color_map
  → Jinja2 renders month_grid.html with colored event dots/chips
```

### Expense Category Chart

```
Browser → GET /api/budget/overview/categories?year=2026
  → OverviewService.get_category_breakdown(calendar_id, year)
    ├── ExpenseRepository.get_by_calendar_year(calendar_id, year)
    └── CategoryRepository.list_expense_categories(calendar_id)
  → Group expenses by category_id, sum amounts
  → Return { categories: [{ name, color, total, budget_limit, percent_used }] }
  → Frontend renders pie/bar chart via Chart.js <canvas> or inline SVG
```

## Database Changes

### New Tables

```sql
-- 1. Event Categories
create table public.event_categories (
  id uuid primary key default gen_random_uuid(),
  calendar_id text not null references public.calendars(id) on delete cascade,
  name text not null,
  color text not null default '#6366f1',   -- hex color
  icon text,                                -- optional emoji or icon key
  sort_order int not null default 0,
  is_default boolean not null default false, -- preset vs custom
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (calendar_id, name)
);

-- 2. Expense Categories
create table public.expense_categories (
  id uuid primary key default gen_random_uuid(),
  calendar_id text not null references public.calendars(id) on delete cascade,
  name text not null,
  color text not null default '#6366f1',
  icon text,
  sort_order int not null default 0,
  budget_limit numeric,                     -- optional per-category monthly limit
  is_default boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (calendar_id, name)
);

-- 3. Notifications
create table public.notifications (
  id uuid primary key default gen_random_uuid(),
  calendar_id text not null references public.calendars(id) on delete cascade,
  recipient_user_id text not null references public.users(id) on delete cascade,
  actor_user_id text references public.users(id) on delete set null,
  type text not null,                       -- 'event_created', 'event_updated', 'event_deleted', 'expense_added', ...
  title text not null,
  body text,
  payload jsonb default '{}',               -- { event_id, expense_id, etc. }
  is_read boolean not null default false,
  email_sent boolean not null default false,
  created_at timestamptz not null default now()
);
create index idx_notifications_recipient_unread
  on public.notifications(recipient_user_id, is_read)
  where is_read = false;

-- 4. Shopping Items
create table public.shopping_items (
  id uuid primary key default gen_random_uuid(),
  calendar_id text not null references public.calendars(id) on delete cascade,
  name text not null,
  is_checked boolean not null default false,
  added_by_user_id text references public.users(id) on delete set null,
  checked_by_user_id text references public.users(id) on delete set null,
  sort_order int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 5. User Preferences (notification settings)
create table public.user_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.users(id) on delete cascade unique,
  email_notifications boolean not null default false,
  notification_types jsonb default '["event_created","event_updated","event_deleted"]',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

### Altered Tables

```sql
-- Add category_id to events (nullable FK)
alter table public.events
  add column category_id uuid references public.event_categories(id) on delete set null;

-- Add category_id to expenses (nullable FK)
alter table public.expenses
  add column category_id uuid references public.expense_categories(id) on delete set null;
```

### Row Level Security (RLS)

All new tables need RLS policies following the same pattern as `carry_forward_overrides`:

```sql
-- Pattern: user can access rows where calendar_id matches their calendar
create policy "Household access" on public.<table>
  for all
  using (
    calendar_id in (
      select u.calendar_id from public.users u
      where u.google_id::text = auth.uid()::text
         or lower(u.email::text) = lower(coalesce(auth.jwt() ->> 'email', ''))
    )
  )
  with check (
    calendar_id in (
      select u.calendar_id from public.users u
      where u.google_id::text = auth.uid()::text
         or lower(u.email::text) = lower(coalesce(auth.jwt() ->> 'email', ''))
    )
  );
```

For `notifications`, add an additional policy restricting reads to `recipient_user_id = auth.uid()` for user-level scoping.

For `user_preferences`, restrict to `user_id` matching the authenticated user.

## Templates (New)

| Template | Route | Content |
|----------|-------|---------|
| `dashboard.html` | `GET /` or `/dashboard` | Today panel, 7-day preview, budget snapshot card, notification feed, quick-add button, shopping summary |
| `shopping.html` | `GET /shopping` | Full shopping list with add form, check-off, delete |
| `notifications.html` | `GET /notifications` | Full notification history with read/unread |
| `partials/notification_bell.html` | Included in `base.html` nav | Bell icon + unread count badge (HTMX polled or SSE) |
| `partials/dashboard_events.html` | HTMX partial | Today's events panel |
| `partials/dashboard_budget.html` | HTMX partial | Budget snapshot card |
| `partials/category_picker.html` | Included in event/expense forms | Dropdown/chip selector for category |
| `partials/expense_chart.html` | HTMX partial on overview | Pie/bar chart by expense category |

## Patterns to Follow

### Pattern 1: Repository → Service → Routes (existing)

Every new module follows the same layered pattern already used throughout the app:

```
routes.py  →  service.py  →  repository.py  →  SupabaseStore
  (HTTP)       (business)     (data mapping)     (REST API)
```

- **Routes** handle HTTP, auth, request/response.
- **Services** handle validation, business rules, orchestration.
- **Repositories** handle Supabase REST calls and dataclass mapping.
- **Schemas** are Pydantic models for request validation.

### Pattern 2: View Routes for HTML Pages

HTML-serving routes go in `views.py` (or `*_views.py`), separate from API `routes.py`:

```python
# app/dashboard/views.py
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request, user=Depends(get_current_user), db=Depends(get_db)):
    context = inject_template_i18n(request, {"request": request, "user": user, ...})
    return templates.TemplateResponse("dashboard.html", context)
```

### Pattern 3: Notification as Side-Effect

Don't build an event bus. Keep it simple: after a successful write in EventService or ExpenseService, call `NotificationEmitter.on_X()`. The emitter is injected at the route level:

```python
# In routes.py
emitter = NotificationEmitter(NotificationService(NotificationRepository(db)))
event = service.create_event(calendar_id, user_id, payload)
emitter.on_event_created(event, user_id, calendar_id)
```

This keeps services pure (no notification dependency) and makes testing easy (don't inject emitter in tests).

### Pattern 4: Chart Rendering — Chart.js

For expense category charts, use **Chart.js** via CDN (`<canvas>` with JS). More interactive than inline SVG (hover tooltips, legend toggle). Load Chart.js only on the budget stats / overview pages to avoid payload on other pages. The app already uses script tags for JS in templates, so this is consistent.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Event Bus / Message Queue Overhead
**What:** Building a pub/sub system for notifications.
**Why bad:** Two users, ~5 notification types. A message queue is overkill.
**Instead:** Direct function calls from routes to NotificationEmitter.

### Anti-Pattern 2: Denormalizing Category Colors onto Events
**What:** Storing the hex color on every event row.
**Why bad:** If category color changes, all events have stale colors.
**Instead:** Look up colors from the small categories table at render time.

### Anti-Pattern 3: Background Task Workers for Email
**What:** Using Celery/RQ for async email sends.
**Why bad:** The app runs as a single Uvicorn process. Adding a task queue is disproportionate for ~2 emails/day.
**Instead:** Inline HTTP POST to Resend API (or SMTP). If it fails, log and move on — the in-app notification still exists.

### Anti-Pattern 4: Separate Category Tables per Domain
**What:** `app/events/categories.py` + `app/budget/categories.py` with duplicated logic.
**Why bad:** Duplicated CRUD, duplicated seeding, duplicated schemas.
**Instead:** Shared `app/categories/` module with separate tables but one repository class handling both.

## Suggested Build Order

Build features in dependency order — foundational data first, then consumers.

### Phase 1: Event Categories + Colors
**Why first:**
- Zero dependencies on other new features.
- Only modifies the events module (additive `category_id` field).
- Enables calendar grid color-coding immediately, which is the most visible UI improvement.
- Creates the category module pattern that expense categories reuse.

**Includes:**
- `event_categories` table + migration + RLS
- `app/categories/` module (repository, service, schemas, routes)
- Modify `app/events/` to pass `category_id`
- Modify `month_grid.html` for color-coded events
- Preset category seeding
- i18n keys for category names

### Phase 2: Expense Categories + Charts
**Why second:**
- Reuses the `app/categories/` module from Phase 1.
- Only extends the budget module (additive `category_id` on expenses).
- Chart rendering is self-contained.

**Includes:**
- `expense_categories` table + migration (with `budget_limit`)
- Extend `app/categories/` for expense categories
- Modify `app/budget/expense_*` to include `category_id`
- Add `get_category_breakdown()` to overview service
- Chart.js integration on budget stats page
- Per-category budget limit alerts
- i18n keys

### Phase 3: Notifications (In-App + Email)
**Why third:**
- Depends on events and expenses being category-aware (richer notification content).
- The notification emitter hooks into event/expense mutation endpoints which should be stable.
- Email is opt-in and can be toggled later.

**Includes:**
- `notifications` + `user_preferences` tables + migrations
- `app/notifications/` module
- NotificationEmitter integrated into event/expense routes
- Notification list page + API
- Email dispatch via Resend (opt-in)
- Bell icon in base.html nav with unread count
- i18n keys

### Phase 4: Shared Shopping List
**Why fourth:**
- Fully independent feature — no dependency on categories or notifications.
- Could theoretically be built in parallel with Phase 3, but sequencing reduces cognitive load.
- Simplest new feature (basic CRUD + text parsing).

**Includes:**
- `shopping_items` table + migration
- `app/shopping/` module
- Shopping list page + API
- Text parsing (comma/newline split)
- i18n keys

### Phase 5: Dashboard Home Page
**Why last:**
- Depends on ALL other features — it aggregates events, budget, notifications, and shopping.
- Building it last means all data sources are stable and tested.
- The aggregator service is simple once individual services are proven.

**Includes:**
- `app/dashboard/` module (aggregator service, views)
- `dashboard.html` template
- Change `GET /` from calendar to dashboard
- Add "Calendar" nav link (since calendar moves to `/calendar`)
- Navigation restructure in `base.html`
- i18n keys

## Sources

- Existing codebase analysis (HIGH confidence — direct code inspection of all modules)
- Established FastAPI + Jinja2 patterns from existing app modules (HIGH confidence)
- Supabase RLS patterns from existing `carry_forward_overrides` migration (HIGH confidence)
- Repository/Service/Routes pattern consistently used across all existing modules (HIGH confidence)
