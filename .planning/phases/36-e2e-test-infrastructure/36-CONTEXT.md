# Phase 36: E2E Test Infrastructure - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Playwright test framework is operational with automatic server targeting, authenticated browser contexts for all 3 test accounts (free, pro, family_plus), and CI-ready configuration. This phase delivers the infrastructure only — no application tests (those are phases 37-39).

</domain>

<decisions>
## Implementation Decisions

### Test Account Strategy
- 3 real Supabase users already exist: free, pro, family_plus
- Pro and family_plus accounts have plans granted via admin page (active subscriptions in Supabase)
- Login method: email/password authentication (NOT Google OAuth) — Playwright fills email + password on `/auth/login` and submits the form
- Credentials stored as environment variables: `E2E_FREE_EMAIL`, `E2E_FREE_PASSWORD`, `E2E_PRO_EMAIL`, `E2E_PRO_PASSWORD`, `E2E_FAMILY_PLUS_EMAIL`, `E2E_FAMILY_PLUS_PASSWORD`
- After browser login, session cookies (`session`, `supabase_refresh`) are preserved and reused across tests via Playwright storage state

### Test Environment Target
- Tests run against the live Railway production deployment: `https://synco-production-e9da.up.railway.app`
- Base URL configured via `E2E_BASE_URL` env var (defaults to Railway URL)
- No local server startup needed — no Playwright `webServer` config
- Test accounts are real Supabase users with test Stripe keys — no impact on real users
- Rate limiting (60/min SlowAPI) is sufficient headroom for E2E suite; no exemption needed initially

### CI Pipeline Configuration
- GitHub Actions workflow triggered on PR to `main` only (not every push, not scheduled)
- Secrets in GitHub Actions: `E2E_FREE_EMAIL`, `E2E_FREE_PASSWORD`, `E2E_PRO_EMAIL`, `E2E_PRO_PASSWORD`, `E2E_FAMILY_PLUS_EMAIL`, `E2E_FAMILY_PLUS_PASSWORD`, `E2E_BASE_URL`
- Screenshots + Playwright traces collected on failure, uploaded as GitHub Actions artifacts
- Non-blocking initially — tests report results but don't block merge until suite stabilizes
- 1 retry per test to handle transient network flakiness
- 30s timeout per test (generous for network round trips to Railway)

### Claude's Discretion
- Playwright config structure (project names, browser selection — Chromium-only is fine for infra phase)
- Auth storage state file naming and directory structure
- GitHub Actions workflow file name and job structure
- Whether to use `playwright/test` fixtures or custom setup scripts for auth
- package.json script additions for running E2E locally

</decisions>

<specifics>
## Specific Ideas

- Auth fixture should log in through the real browser UI (navigate to `/auth/login`, fill form, submit) — not cookie injection — to verify the login flow itself works
- Storage state files should be generated once in a `globalSetup` and reused across all tests in a project
- Three Playwright projects: `free`, `pro`, `family-plus` — each using its respective authenticated storage state

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Auth flow
- `app/auth/routes.py` — Login/register routes, session cookie creation, OAuth callback
- `app/auth/supabase_auth.py` — `supabase_password_sign_in()` for email/password auth
- `app/auth/dependencies.py` — `get_current_user()` reads `session` + `supabase_refresh` cookies

### App configuration
- `config.py` — Settings class with all env vars (Supabase, Stripe, JWT config)
- `main.py` — FastAPI app setup, middleware stack, router includes, exception handlers

### Existing test patterns
- `tests/conftest.py` — Current pytest fixtures (InMemoryStore, test_client, authenticated_client)
- `tests/test_billing.py` — `TestStripeLivePurchaseFlow` class with `skipif` gating pattern
- `.planning/quick/260325-cyy-test-stripe-purchase-of-plan-with-fake-a/` — Recent Stripe integration test quick task

### Deployment
- `railway.toml` — Railway deployment config
- `.github/` — Existing GitHub Actions workflows (if any)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `package.json` already exists with npm/node tooling (Tailwind build) — Playwright can be added as devDependency
- `.github/` directory exists — GitHub Actions infrastructure already in place
- `app/auth/supabase_auth.py::supabase_password_sign_in()` — The exact auth function E2E tests will exercise through the browser

### Established Patterns
- Existing 593 pytest tests use InMemoryStore (unit tests) — E2E tests are a separate layer targeting the real deployed app
- Stripe live tests use `@pytest.mark.skipif(not os.environ.get("STRIPE_SECRET_KEY"))` gating — E2E tests should use similar env-var gating
- App serves server-rendered Jinja2 + HTMX pages — E2E tests interact with real HTML, not a SPA

### Integration Points
- Login form at `/auth/login` — Playwright fills email/password inputs and submits
- Session cookies (`session`, `supabase_refresh`) — Playwright captures these after login for storage state
- Middleware stack: LicenseCheck → SecurityHeaders → CORS → SlowAPI (60/min) → StaticCache → SessionValidation

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 36-e2e-test-infrastructure*
