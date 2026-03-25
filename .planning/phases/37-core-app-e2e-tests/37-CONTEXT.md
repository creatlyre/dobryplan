# Phase 37: Core App E2E Tests - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Auth flow, calendar views, dashboard, and notifications render correctly and function in the browser. This phase writes the actual E2E test specs using Phase 36's infrastructure (Playwright projects, auth storage states, CI config). No new infrastructure — only test files.

</domain>

<decisions>
## Implementation Decisions

### Test Data Strategy
- All tests are **read-only / non-destructive** — no form submissions that create, modify, or delete production data
- Event creation modal: open → verify fields present → close without saving
- Calendar navigation: click through months/days, verify rendering — no writes
- Dashboard: verify sections render with real data, no mutations
- This avoids cleanup logic and protects production users' data
- If a test needs to verify form submission behavior, it stops at verifying the modal/form opens correctly with expected fields

### Auth Test Scope
- **1 happy path + 1 sad path per flow** — matches success criteria exactly
- Login: valid credentials → lands on dashboard; wrong password → visible error message
- Register page: verify form renders with expected fields — do NOT submit (would create real user)
- Session expiry/redirect: covered in Phase 39 (Error Resilience), not here
- Test the real browser login flow (navigate to `/auth/login`, fill form, submit) — consistent with Phase 36's auth fixture approach

### Calendar Verification Approach
- Month view: verify grid renders with day cells, navigation arrows work (prev/next month)
- Day click: verify it opens the event entry modal (then close without saving)
- Event indicators: verify color-coded dots/markers appear for days with events (test accounts should have some existing events)
- No event CRUD — just rendering and navigation

### Dashboard Verification Approach
- Dashboard is the home page (`/`) — verify it loads after login
- Verify key sections are present: today's events area, budget snapshot, quick-add chooser button
- 7-day preview section renders
- No interaction with quick-add (that creates data)

### Notification Verification Approach
- **UI-presence only** — no content assertions
- Bell icon renders in the navbar for authenticated users
- Clicking bell opens the notification dropdown container
- Notification feed page (`/notifications`) loads the list container
- No assertions on notification count or content (depends on uncontrollable partner activity)

### Test File Organization
- One test file per area: `tests/e2e/test_auth.spec.ts`, `test_calendar.spec.ts`, `test_dashboard.spec.ts`, `test_notifications.spec.ts`
- Each file uses the appropriate Playwright project (pro account for full access, free for basic checks)
- Tests within a file are independent — no ordering dependencies

### Claude's Discretion
- Exact Playwright selectors (data-testid vs CSS selectors vs text content)
- How many month navigations to test (1-2 is sufficient)
- Whether to split auth tests across projects or run all under one
- Dashboard section selector specificity
- Test describe/it naming conventions

</decisions>

<specifics>
## Specific Ideas

- Use `pro` project as the primary test account (has full feature access) for calendar, dashboard, and notification tests
- Auth tests should use their own login flow (not the stored session) to verify the actual login page works
- Calendar tests should verify the month grid has 28-31 day cells (not hardcoded)
- Dashboard test should verify the page title or heading contains expected text in Polish (default locale)

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 36 Infrastructure (dependency)
- `.planning/phases/36-e2e-test-infrastructure/36-CONTEXT.md` — Playwright setup decisions, project names, auth strategy, CI config

### Auth flow
- `app/auth/routes.py` — `GET /auth/login`, `POST /auth/password-login`, `GET /auth/register`, `POST /auth/register`
- `app/templates/login.html` — Login form template (field names, submit button)
- `app/templates/register.html` — Register form template

### Calendar views
- `app/views/calendar_routes.py` — `GET /calendar` (main page), `GET /calendar/month` (HTMX month grid)
- `app/templates/calendar.html` — Calendar page template with month grid, day cells, event modal
- `app/templates/partials/event_entry_modal.html` — Event creation modal

### Dashboard
- `app/dashboard/routes.py` — `GET /` (home page, HTML response)
- `app/templates/dashboard.html` — Dashboard with today's events, budget snapshot, quick-add

### Notifications
- `app/notifications/views.py` — `GET /notifications/badge`, `GET /notifications/dropdown`
- `app/notifications/routes.py` — `GET /api/notifications`, `GET /api/notifications/unread-count`
- `app/templates/base.html` — Bell icon in navbar (`#notification-bell`, `#notification-bell-container`)

</canonical_refs>

<code_context>
## Existing Code Insights

### Key Selectors (from templates)
- Notification bell: `#notification-bell` button, `#notification-bell-container` wrapper
- Quick-add chooser: `#qa-chooser-title` modal
- Event entry modal: referenced in `partials/event_entry_modal.html`
- Dashboard expense modal: `#dash-expense-modal`

### Route Patterns
- Auth pages: `/auth/login`, `/auth/register` (GET = form, POST = submit)
- Calendar: `/calendar` (full page), `/calendar/month?year=X&month=Y` (HTMX partial)
- Dashboard: `/` (root = dashboard for authenticated users)
- Notifications API: `/api/notifications`, `/api/notifications/unread-count`
- Notification views: `/notifications/badge`, `/notifications/dropdown` (HTML partials)

### Established Patterns
- Server-rendered HTML with HTMX for partial updates
- Jinja2 templates with `base.html` layout
- Polish as default locale — page titles and headings will be in Polish
- `get_current_user` dependency redirects unauthenticated users to `/auth/login`

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 37-core-app-e2e-tests*
