# Project Research Summary

**Project:** CalendarPlanner v3.0
**Domain:** Household calendar + budget app — Dashboard, Notifications & Categories
**Researched:** 2026-03-22
**Confidence:** HIGH

## Executive Summary

CalendarPlanner v3.0 extends a two-person household calendar and budget app (FastAPI + Jinja2/HTMX + Supabase) with five feature groups: event categories with color-coded calendar grid, expense categories with pie/bar charts and per-category budget limits, a shared shopping list, an in-app partner notification feed, and a unified dashboard home page. The existing stack handles all requirements with only two new dependencies — Chart.js via CDN for charts and aiosmtplib for optional email alerting. The architecture follows the proven repository-service-routes layered pattern already used across all modules, with 4 new Supabase tables and nullable FK additions to the existing events and expenses tables.

The recommended approach is to build features in strict dependency order: categories first (foundational data models), then shopping list (independent), then notifications (hooks into established CRUD), and dashboard last (read-only aggregator over all sources). This ordering emerged independently from all four research files and minimizes rework. The key risks are dashboard N+1 query latency over Supabase REST (mitigated by parallel fetching), large blast radius when adding category_id to existing models (mitigated by nullable fields with defaults), and over-notification in a two-person context (mitigated by batching and suppression rules).

Email notifications should be deferred to v3.1. The in-app notification feed satisfies the core "what did my partner change?" use case without introducing SMTP infrastructure, DNS configuration, and deliverability concerns. This keeps v3.0 focused on high-value, low-risk features with well-established implementation patterns.

## Key Findings

### Recommended Stack

| Technology | Purpose | Rationale |
|---|---|---|
| **Chart.js 4.5.1 (CDN)** | Pie/bar charts for expense category breakdown | 67KB gzipped, CDN script tag consistent with existing no-build approach. Covers pie + bar with tooltips and legends. |
| **aiosmtplib 5.1.0** | Async email sending (if email notifications enabled) | Native asyncio SMTP client, zero dependencies. Pairs with FastAPI BackgroundTasks for fire-and-forget delivery. |
| **FastAPI BackgroundTasks** | Non-blocking email dispatch | Already built-in. No Celery/Redis needed for 2-user volume. |
| **CSS custom properties** | Event category color coding on calendar grid | Native, no library. --cat-work, --cat-personal, etc. |

**No changes to core stack.** Python/FastAPI, Supabase (PostgreSQL), Jinja2 templates, prebuilt Tailwind CSS, httpx — all remain as-is.

**What NOT to use:** WebSockets (polling is sufficient for 2 users), Celery/Redis (overkill), React/Vue/HTMX framework additions (stay with vanilla JS + HTMX), npm/bundler for Chart.js (CDN only), SQLAlchemy/ORM (continue SupabaseStore pattern).

### Expected Features

**Must Have (v3.0):**

| Feature | Complexity | Dependencies |
|---|---|---|
| Event categories with color-coded calendar grid | Medium | New table, FK on events |
| Expense categories with filter/group | Medium | New table, FK on expenses |
| Expense category pie/bar charts (Chart.js) | Low | Expense categories |
| Per-category budget limits with 80%/100% alerts | Medium | Expense categories |
| Shared shopping list (text + checked/unchecked) | Low-Medium | Independent |
| Shopping list string parsing ("milk, bread, eggs" -> 3 items) | Low | Shopping list |
| In-app notification feed (partner activity log) | Medium | Events + expenses CRUD stable |
| Dashboard home page (today's events, budget snapshot, notifications, shopping) | Low | All other features |
| Dashboard quick-add (reuse existing modals) | Low | Dashboard |

**Defer to v3.1+:**

| Feature | Reason |
|---|---|
| Email notifications | SMTP infrastructure disproportionate for v3.0; in-app feed sufficient |
| Expense auto-categorization | Over-engineered; "remember last category for same name" is enough |
| Full color picker | Curated 10-12 color palette is better UX on dark theme |
| Multiple shopping lists | One list sufficient for 2-person household |
| Dashboard widget customization | Fixed layout appropriate for 2 users with identical data |
| Notification preference granularity | Single on/off toggle sufficient; per-type toggles add complexity |

### Architecture Approach

**4 new modules** following existing layered pattern:

| Module | Responsibility | Key Pattern |
|---|---|---|
| app/categories/ | Shared category CRUD for events & expenses (separate tables, shared logic) | repository-service-routes |
| app/shopping/ | Shopping list CRUD + comma/newline text parsing | repository-service-routes |
| app/notifications/ | In-app feed, NotificationEmitter as side-effect in routes | Emitter called after CRUD success |
| app/dashboard/ | Read-only aggregator over all other services | Composition, no owned data |

**4 new Supabase tables:** event_categories, expense_categories, notifications, shopping_items (+ user_preferences for notification toggle). All need RLS policies matching existing household-access pattern.

**2 altered tables:** events + expenses gain nullable category_id FK columns.

**Key architectural decisions:**
- Categories looked up at render time (not denormalized onto events) to avoid stale color drift
- Notifications triggered by direct function calls from routes to NotificationEmitter, not an event bus
- Dashboard service composes other services, never accesses repositories directly
- Shopping list uses HTMX polling (hx-trigger="every 30s"), not WebSocket/SSE
- Chart.js loaded only on pages that need charts, not in base.html

### Critical Pitfalls

| # | Pitfall | Severity | Mitigation | Phase |
|---|---|---|---|---|
| 1 | **Dashboard N+1 REST queries** — 6-10 sequential Supabase HTTP calls causing 1-4s latency | Critical | Parallelize with ThreadPoolExecutor or Supabase RPC; simple dict cache with 30-60s TTL | Dashboard |
| 2 | **category_id blast radius** — adding FK to events/expenses touches 15+ files, breaks test fixtures | Critical | Nullable with default None; staged rollout (migration - model - UI); never require category on existing records | Categories |
| 3 | **Over-notification** — every action by User A spams User B; bulk imports generate hundreds | Critical | Batch within 5-min windows; suppress during imports; never notify actor; respect event visibility | Notifications |
| 5 | **Color accessibility on dark theme** — category colors invisible or indistinguishable on glassmorphism UI | Critical | Curated palette of 8-10 colors tested against dark background; always pair color with text label; use Tailwind 400-weight variants | Event Categories |
| 7 | **False budget alerts from recurring expenses** — static limits + recurring/seasonal variation = constant noise | Moderate | Soft informational warnings only (never blocking); include recurring in calculations; default to no limits; ship limits after charts | Expense Categories |

**Additional moderate risks:** unbounded notification storage (30-day retention + pagination), i18n key parity across en.json/pl.json (parity test), category presets vs. custom two-source-of-truth (all categories in DB, seeded not hardcoded), chart library bloat (lazy-load Chart.js only on stats pages).

## Implications for Roadmap

All four research files independently converged on the same build order. Phases should follow strict dependency ordering:

### Phase 1: Event Categories & Calendar Grid Colors
**Rationale:** Zero dependencies on other new features. Creates the app/categories/ module pattern reused by expense categories. Most visible UI improvement (color-coded calendar). Lowest risk starting point.
**Delivers:** event_categories table, category CRUD API, 5 preset categories seeded per calendar, color-coded event chips on month grid, category picker on event forms.
**Pitfalls to avoid:** #2 (nullable FK, staged rollout), #5 (curated dark-theme palette), #13 (all categories in DB).
**Research needed:** No — well-established patterns.

### Phase 2: Expense Categories + Charts + Budget Limits
**Rationale:** Reuses app/categories/ module from Phase 1. Chart.js integration is self-contained. Budget limits are natural extension of category model.
**Delivers:** expense_categories table, category tagging on expenses, pie/bar charts via Chart.js, optional per-category budget limits with soft 80%/100% warnings.
**Pitfalls to avoid:** #2 (nullable FK on expenses), #7 (soft warnings only, include recurring), #8 (lazy-load Chart.js).
**Research needed:** No — extends Phase 1 patterns.

### Phase 3: Shared Shopping List
**Rationale:** Fully independent, no cross-dependencies. Simplest new feature (basic CRUD + text parsing). Validates the new-module pattern before the more complex notification system.
**Delivers:** shopping_items table, shopping list page, add/check-off/delete items, comma/newline text parsing, HTMX polling for partner sync.
**Pitfalls to avoid:** #6 (no WebSocket — HTMX polling only), #10 (split on commas/newlines only, no NLP).
**Research needed:** No — standard CRUD.

### Phase 4: In-App Notification Feed
**Rationale:** Depends on events and expenses being category-aware for richer content. CRUD hooks must be stable before attaching side-effects. Most complex new feature — benefits from lessons learned in prior phases.
**Delivers:** notifications + user_preferences tables, NotificationEmitter side-effects on event/expense/shopping mutations, bell icon with unread count in nav, notification list page, 30-day retention policy.
**Pitfalls to avoid:** #3 (batch within 5-min windows, suppress imports, never self-notify), #9 (30-day retention, pagination), #12 (i18n parity).
**Research needed:** Notification batching strategy may benefit from /gsd-research-phase to validate the 5-minute window approach.

### Phase 5: Dashboard Home Page
**Rationale:** Aggregates ALL other features — must be built last when data sources are stable and tested. Read-only composition means lowest risk of breaking other modules.
**Delivers:** dashboard.html as new GET / landing page, today's events panel, 7-day preview, budget snapshot with category breakdown, unread notification count, shopping list summary, quick-add buttons.
**Pitfalls to avoid:** #1 (parallel fetch with ThreadPoolExecutor, performance budget <500ms), #11 (graceful widget degradation, service composition only).
**Research needed:** Dashboard parallel-fetch strategy may benefit from /gsd-research-phase to benchmark ThreadPoolExecutor vs. Supabase RPC.

### Research Flags

| Phase | Research Needed? | Reasoning |
|---|---|---|
| Phase 1: Event Categories | **No** | Follows existing module patterns exactly |
| Phase 2: Expense Categories | **No** | Chart.js CDN integration is well-documented |
| Phase 3: Shopping List | **No** | Simplest new feature |
| Phase 4: Notifications | **Maybe** | 5-min window batching is the one novel pattern |
| Phase 5: Dashboard | **Maybe** | ThreadPoolExecutor vs. RPC tradeoff affects implementation |

## Confidence Assessment

| Area | Confidence | Notes |
|---|---|---|
| Stack | **HIGH** | Only 2 new deps (Chart.js CDN, aiosmtplib). Both well-documented, high-download libraries. Rest is existing stack. |
| Features | **HIGH** | Features derived from established household app patterns (Google Calendar, YNAB, Cozi). Clear scope boundaries. |
| Architecture | **HIGH** | Follows existing codebase patterns exactly. All 4 new modules use proven repo-service-routes layering. Direct code inspection confirms compatibility. |
| Pitfalls | **HIGH** | 13 pitfalls identified from direct codebase analysis, not theoretical. Mitigations are concrete and tested against actual code patterns. |

**Gaps to address during planning:**
- Dashboard parallel-fetch approach needs benchmarking (ThreadPoolExecutor vs. Supabase RPC vs. simple sequential with caching)
- Notification batching window (5 minutes) is a reasonable default but should be validated during Phase 4 planning
- Chart.js vs. CSS/SVG for pie charts — STACK recommends Chart.js, PITFALLS suggests CSS/SVG first. **Recommendation: Use Chart.js** — pie charts require it, and 67KB gzipped is acceptable for the stats page only
- Email notifications scope (v3.0 vs v3.1) — STACK includes aiosmtplib, FEATURES defers email. **Recommendation: Defer email to v3.1.** Install aiosmtplib only when needed

## Sources

- **STACK.md:** Chart.js 4.5.1 (npmjs.com, chartjs.org docs), aiosmtplib 5.1.0 (pypi.org, readthedocs), FastAPI BackgroundTasks (fastapi.tiangolo.com)
- **FEATURES.md:** Domain patterns from Google Calendar, YNAB, Cozi Family Organizer, FamilyWall, Goodbudget. Existing codebase analysis (models.py, expense_schemas.py, month_grid.html, budget_stats.html)
- **ARCHITECTURE.md:** Direct code inspection of all existing modules. Supabase RLS patterns from existing migrations. Repository/Service/Routes pattern analysis
- **PITFALLS.md:** Direct codebase analysis of supabase_store.py (sync httpx singleton), repository mapper patterns, budget_stats.html (CSS bar charts), dark theme classes in month_grid.html. WCAG 2.1 contrast requirements
