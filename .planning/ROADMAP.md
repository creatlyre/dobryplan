# Roadmap: CalendarPlanner

## Milestones

- [x] v1.0 milestone - Phases 1-7 shipped 2026-03-19 (22/22 plans complete). Archive: .planning/milestones/v1.0-ROADMAP.md
- [x] v1.1 milestone - Phases 8-11 shipped 2026-03-20 (10/10 plans complete). Archive: .planning/milestones/v1.1-ROADMAP.md
- [x] v2.0 milestone — Budget Tracker - Phases 12-17 shipped 2026-03-20 (230 tests passing). Archive: .planning/milestones/v2.0-ROADMAP.md
- [x] v2.1 milestone — Privacy, Reminders & Multi-Year Budget - Phases 18-22 shipped 2026-03-22 (270 tests passing). Archive: .planning/milestones/v2.1-ROADMAP.md
- [x] v3.0 milestone — Dashboard, Notifications & Categories - Phases 23-27 shipped 2026-03-23 (331 tests passing). Archive: .planning/milestones/v3.0-ROADMAP.md
- [x] v4.0 milestone — Monetization Foundation (SaaS primary + self-hosted purchase option) - Phases 28-33 shipped 2026-03-23 (446 tests passing). Archive: .planning/milestones/v5.0-ROADMAP.md (v4.0 archived as part of v5.0 snapshot)
- [x] v5.0 milestone — Growth & Conversion - Phases 34-35 shipped 2026-03-25 (593 tests passing). Archive: .planning/milestones/v5.0-ROADMAP.md
- [ ] v5.1 milestone — Stripe E2E Verification - Phases 36-39 (Playwright browser tests for full app verification)

## Phases

### v5.1 Stripe E2E Verification (Phases 36-39)

- [ ] **Phase 36: E2E Test Infrastructure** - Playwright setup, app server fixture, authenticated contexts, CI config
- [ ] **Phase 37: Core App E2E Tests** - Auth, calendar, dashboard, and notification browser tests
- [ ] **Phase 38: Gated Features & Entitlements E2E** - Budget, shopping, sync, and plan access control tests
- [ ] **Phase 39: Billing, Stripe & Error Resilience E2E** - Pricing, checkout flow, billing portal, and error handling tests

## Phase Details

### Phase 36: E2E Test Infrastructure
**Goal**: Playwright test framework is operational with automatic server startup, authenticated browser contexts for all 3 test accounts, and CI-ready configuration
**Depends on**: Nothing (first phase of v5.1)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05
**Success Criteria** (what must be TRUE):
  1. `npx playwright test` runs against the live app without manual server startup
  2. Test accounts (free, pro, family_plus) log in automatically and preserve sessions across tests
  3. Failed tests produce screenshots and traces for debugging
  4. Tests run headless in CI configuration with proper timeouts and retries
**Plans:** 2 plans
Plans:
- [ ] 36-01-PLAN.md — Playwright setup, multi-role auth, smoke test
- [ ] 36-02-PLAN.md — GitHub Actions CI workflow

### Phase 37: Core App E2E Tests
**Goal**: Auth flow, calendar views, dashboard, and notifications render correctly and function in the browser
**Depends on**: Phase 36
**Requirements**: AUTH-E2E-01, AUTH-E2E-02, AUTH-E2E-03, AUTH-E2E-04, CAL-E2E-01, CAL-E2E-02, CAL-E2E-03, DASH-E2E-01, DASH-E2E-02, DASH-E2E-03, NOTF-E2E-01, NOTF-E2E-02
**Success Criteria** (what must be TRUE):
  1. Login with valid credentials lands on dashboard; invalid credentials show visible error
  2. Calendar month and day views render with navigation and event creation modal
  3. Dashboard loads as home page with today's events, budget snapshot, and quick-add chooser
  4. Notification bell appears in navbar and feed page loads notification list
**Plans:** 2 plans
Plans:
- [ ] 37-01-PLAN.md — Auth flow + calendar view E2E tests
- [ ] 37-02-PLAN.md — Dashboard + notification UI E2E tests

### Phase 38: Gated Features & Entitlements E2E
**Goal**: Plan-gated features enforce correct access control and render properly for authorized users
**Depends on**: Phase 37
**Requirements**: BUD-E2E-01, BUD-E2E-02, BUD-E2E-03, SHOP-E2E-01, SHOP-E2E-02, SYNC-E2E-01, SYNC-E2E-02, GATE-E2E-01, GATE-E2E-02, GATE-E2E-03, GATE-E2E-04
**Success Criteria** (what must be TRUE):
  1. Free user gets upgrade redirect when accessing /shopping, /budget/stats, /budget/import
  2. Pro user accesses shopping list and budget stats pages without redirect
  3. Budget overview, expenses, and income pages render for authenticated users
  4. Google Sync section shows "not connected" state for test accounts (no Google association)
**Plans**: 1 plan
Plans:
- [ ] 38-01-PLAN.md — Gating tests (free blocked + API 403) and feature render tests (budget, shopping, sync)

### Phase 39: Billing, Stripe & Error Resilience E2E
**Goal**: Pricing-to-checkout flow works end-to-end and error scenarios produce graceful responses
**Depends on**: Phase 38
**Requirements**: BILL-E2E-01, BILL-E2E-02, BILL-E2E-03, BILL-E2E-04, BILL-E2E-05, ERR-E2E-01, ERR-E2E-02, ERR-E2E-03
**Success Criteria** (what must be TRUE):
  1. Pricing page renders plan cards for both authenticated and unauthenticated visitors
  2. Checkout API returns a valid checkout.stripe.com URL (redirect verified, payment form not submitted)
  3. Billing settings page shows current plan; portal API returns billing.stripe.com URL for paid users
  4. Unauthenticated or expired session requests redirect to login page
  5. API endpoints return proper error JSON for invalid requests
**Plans:** 2 plans
Plans:
- [ ] 39-01-PLAN.md — Billing E2E tests (pricing, checkout, settings, portal)
- [ ] 39-02-PLAN.md — Error resilience E2E tests (auth redirects, API errors)

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 36. E2E Test Infrastructure | 0/? | Not started | - |
| 37. Core App E2E Tests | 0/2 | Planned | - |
| 38. Gated Features & Entitlements E2E | 0/? | Not started | - |
| 39. Billing, Stripe & Error Resilience E2E | 0/2 | Planned | - |

<details>
<summary>✅ v5.0 Growth & Conversion (Phases 34-35) — SHIPPED 2026-03-25</summary>

- [x] Phase 34: Hero Landing Page (1/1 plans) — completed 2026-03-24
  Plans:
  - [x] 34-01-PLAN.md — Enhanced hero, social proof, SEO meta, i18n + tests
- [x] Phase 35: Fix Logout Redirect (1/1 plans) — completed 2026-03-24
  Plans:
  - [x] 35-01-PLAN.md — Fix logout endpoint redirect + tests

</details>

<details>
<summary>✅ v4.0 Monetization Foundation (Phases 28-33) — SHIPPED 2026-03-23</summary>

- [x] Phase 28: Licensing and Commercial Terms Foundation (2 plans) — completed 2026-03-23
- [x] Phase 29: Billing, Plans, and Entitlements Core (2 plans) — completed 2026-03-23
- [x] Phase 30: SaaS Production Platform and Operations (2 plans) — completed 2026-03-23
- [x] Phase 31: Paid Self-Hosted Distribution (2 plans) — completed 2026-03-23
- [x] Phase 32: Mobile Distribution Path (PWA + Android Wrapper) (2 plans) — completed 2026-03-23
- [x] Phase 33: Go-to-Market, Pricing, and Launch Funnel (3 plans) — completed 2026-03-23

</details>

<details>
<summary>✅ v3.0 Dashboard, Notifications & Categories (Phases 23-27) — SHIPPED 2026-03-23</summary>

- [x] Phase 23: Event Categories & Colors (2/2 plans) — completed 2026-03-22
- [x] Phase 24: Expense Categories & Charts (2/2 plans) — completed 2026-03-23
- [x] Phase 25: Shopping List (2/2 plans) — completed 2026-03-23
- [x] Phase 26: Notifications (3/3 plans) — completed 2026-03-23
- [x] Phase 27: Dashboard (2/2 plans) — completed 2026-03-23

</details>

<details>
<summary>✅ v2.1 Privacy, Reminders & Multi-Year Budget (Phases 18-22) — SHIPPED 2026-03-21</summary>

- [x] Phase 18: Event Privacy (2/2 plans) — completed 2026-03-20
- [x] Phase 19: Reminder UI (1/1 plan) — completed 2026-03-20
- [x] Phase 20: Multi-Year Budget (2/2 plans) — completed 2026-03-21
- [x] Phase 21: Year-over-Year Comparison (1/1 plan) — completed 2026-03-21
- [x] Phase 22: Historical Year Import (1/1 plan) — completed 2026-03-21

</details>

<details>
<summary>✅ v2.0 Budget Tracker (Phases 12-17) — SHIPPED 2026-03-20</summary>

- [x] Phase 12: Budget Data Foundation & Settings UI (3/3 plans) — completed 2026-03-20
- [x] Phase 13: Income Calculation Engine (3/3 plans) — completed 2026-03-20
- [x] Phase 14: Expense Management (3/3 plans) — completed 2026-03-20
- [x] Phase 15: Year Overview Dashboard (1/1 plan) — completed 2026-03-20
- [x] Phase 16: Overview Month Detail (2/2 plans) — completed 2026-03-20
- [x] Phase 17: Performance Optimization (2/2 plans) — completed 2026-03-20

</details>

---

*Roadmap updated: 2026-03-25 — v5.1 Stripe E2E Verification roadmap created (Phases 36-39)*
