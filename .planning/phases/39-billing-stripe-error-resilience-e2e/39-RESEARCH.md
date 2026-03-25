# Phase 39: Billing, Stripe & Error Resilience E2E — Research

**Date:** 2026-03-25
**Discovery Level:** 0 (all patterns established in Phases 36-38)
**New Dependencies:** None

## Standard Stack

- **Test Framework:** Playwright (`@playwright/test`) — already installed
- **Config:** `e2e/playwright.config.ts` — 3 role-based projects (free, pro, family-plus)
- **Auth Strategy:** `storageState` files per role, created by `e2e/auth.setup.ts`
- **Target:** Live Railway deployment (`E2E_BASE_URL` env var)

## Architecture Patterns

### Established E2E Patterns (from Phases 36-38)
1. **Role-based projects:** `free`, `pro`, `family-plus` projects with per-role storageState
2. **Unauthenticated tests:** `test.use({ storageState: { cookies: [], origins: [] } })` for no-auth context
3. **Read-only testing:** Call APIs, verify responses, but never mutate production data
4. **Response status checks:** `const response = await page.goto('/path'); expect(response?.status()).toBe(200);`
5. **API-level tests:** `page.request.get()` / `page.request.post()` for JSON API verification
6. **HTMX wait pattern:** `Promise.all([page.waitForResponse(...), page.click(...)])` for HTMX-driven content

### Billing API Contracts (from codebase)
- `POST /api/billing/checkout` — body: `{plan: "pro"|"family_plus"|"self_hosted", billing_period: "monthly"|"annual"}` → `{url: "https://checkout.stripe.com/..."}` (200) or 401/422/400
- `POST /api/billing/portal` — no body → `{url: "https://billing.stripe.com/..."}` (200) or 400 `{detail: "No billing account found"}`
- `GET /pricing` — public page, renders plan cards (Free, Pro, Family+, Self-Hosted)
- `GET /billing/settings` — authenticated, shows current plan + status + manage button

### Auth Redirect Behavior (from `main.py` line 334)
- 401 on `/invite` or `/dashboard` → 302 redirect to `/auth/login`
- 403 on `/admin/*` → 302 redirect to `/dashboard`
- Other 401s → standard JSON error response
- Note: `/billing/settings` requires `get_current_user` dependency which raises 401 → but `/billing/settings` is NOT in the `auth_redirect_handler` path list, so it returns standard 401 (not redirect)

### Pricing Page Structure (from `pricing.html`)
- 3 SaaS plan cards in a grid: Free (h3), Pro (h3, highlighted), Family+ (h3)
- 1 Self-Hosted section below the grid
- Monthly/annual toggle with `#billing-toggle` button
- Checkout buttons: `onclick="checkout('pro')"` / `checkout('family_plus')` / `checkout('self_hosted')`
- Free plan has link to `/auth/login` instead of checkout button
- JS `checkout()` function: POSTs to `/api/billing/checkout`, redirects to returned URL

### Billing Settings Structure (from `billing_settings.html`)
- Plan badge: `.rounded-full` span with plan name text (Pro/Family+/Free)
- Status badge: emerald for active, amber for past_due, red for canceled
- `#manage-sub-btn` button: visible only when `user_plan != 'free' and has_stripe_customer`
- JS on `#manage-sub-btn` click: POSTs to `/api/billing/portal`, redirects to returned URL

## Requirement Mapping

| REQ ID | Requirement | Test Strategy |
|--------|-------------|---------------|
| BILL-E2E-01 | Pricing page renders for auth + unauth | Navigate `/pricing` in both contexts, verify 3+ plan headings |
| BILL-E2E-02 | Checkout API returns valid Stripe URL | `page.request.post('/api/billing/checkout')` as pro, verify URL prefix |
| BILL-E2E-03 | Billing settings shows current plan | Navigate `/billing/settings` as pro, verify plan label + status |
| BILL-E2E-04 | Portal API returns valid Stripe URL | `page.request.post('/api/billing/portal')` as pro, verify URL prefix |
| BILL-E2E-05 | Portal fails for free user | `page.request.post('/api/billing/portal')` as free → 400 + error detail |
| ERR-E2E-01 | Unauth page access redirects to login | Navigate `/dashboard` without auth → 302 to `/auth/login` |
| ERR-E2E-02 | API without auth returns 401 | `request.post('/api/billing/checkout')` without cookies → 401 JSON |
| ERR-E2E-03 | API invalid payload returns error | POST checkout with `{plan: "invalid"}` → 422 validation error |

## Don't Hand-Roll

- Playwright auth setup (already in `auth.setup.ts`)
- Unauthenticated context pattern (established in Phase 37 `test_auth.spec.ts`)

## Common Pitfalls

1. **Auth redirect only covers `/invite` and `/dashboard`**: The `auth_redirect_handler` in `main.py` only redirects 401 on those two paths. `/billing/settings` will get a standard 401 response when unauthenticated, NOT a redirect. For browser navigation, the response may trigger different behavior depending on how FastAPI handles it.
2. **Pydantic validation returns 422 (not 400)**: Invalid `plan` values hit Pydantic's `field_validator` which returns 422 Unprocessable Entity.
3. **Free user portal 400 vs no Stripe customer**: The portal endpoint checks `sub.stripe_customer_id` — free test user has no subscription at all, so `sub` is `None`, triggering the 400 with "No billing account found".

## Validation Architecture

### Test Files
- `e2e/tests/test_billing.spec.ts` — BILL-E2E-01 through BILL-E2E-05
- `e2e/tests/test_errors.spec.ts` — ERR-E2E-01 through ERR-E2E-03

### Automated Verification
All tests fully automated via Playwright. No manual-only verifications needed.

### Run Commands
- Quick: `npx playwright test --config=e2e/playwright.config.ts e2e/tests/test_billing.spec.ts e2e/tests/test_errors.spec.ts --reporter=line --retries=0`
- Full: `npx playwright test --config=e2e/playwright.config.ts --reporter=line`

## RESEARCH COMPLETE
