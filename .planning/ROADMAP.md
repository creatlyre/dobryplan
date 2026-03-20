# Roadmap: CalendarPlanner

## Milestones

- [x] v1.0 milestone - Phases 1-7 shipped 2026-03-19 (22/22 plans complete). Archive: .planning/milestones/v1.0-ROADMAP.md
- [x] v1.1 milestone - Phases 8-11 shipped 2026-03-20 (10/10 plans complete). Archive: .planning/milestones/v1.1-ROADMAP.md
- [x] v2.0 milestone — Budget Tracker - Phases 12-15 shipped 2026-03-20 (214 tests passing)

## Phases

- [x] **Phase 12: Budget Data Foundation & Settings UI** — Database models, settings page for rates/costs/balance, nav integration, i18n setup
 (completed 2026-03-20)
- [x] **Phase 13: Income Calculation Engine** — Monthly hours entry per rate, gross/net computation, additional household earnings
 (completed 2026-03-20)
- [x] **Phase 14: Expense Management** — Recurring and one-time expense CRUD with auto-application
 (completed 2026-03-20)
- [x] **Phase 15: Year Overview Dashboard** — 12-month financial table with running balance and live recalculation
 (completed 2026-03-20)
- [x] **Phase 16: Overview month detail - clickable months showing one-time expense breakdown** — Accordion UI with inline CRUD
 (completed 2026-03-20)
- [x] **Phase 17: Performance optimization - faster page loads and API responses** — Prebuilt Tailwind CSS, connection pooling, static serving
 (completed 2026-03-20)

## Phase Details

### Phase 12: Budget Data Foundation & Settings UI
**Goal**: Users can configure their budget parameters (hourly rates, monthly costs, initial balance) via a dedicated settings page integrated into the app navigation
**Depends on**: Nothing (new module)
**Requirements**: BSET-01, BSET-02, BSET-03, BSET-04, BSET-05, BL-01
**Success Criteria** (what must be TRUE):
  1. User can navigate to budget settings from the main app navigation bar
  2. User can set 3 hourly rates in PLN, flat monthly ZUS+accounting costs, and initial bank account balance — all values persisted across sessions
  3. User can return to settings at any time and update any value with changes saved immediately
  4. Budget settings UI renders in Polish by default (English available if i18n wiring is low effort)
**Plans**: 3 plans

Plans:
- [ ] 12-01-PLAN.md — Budget data layer + API + i18n keys
- [ ] 12-02-PLAN.md — Settings UI + navigation integration
- [ ] 12-03-PLAN.md — Integration tests + human verification

### Phase 13: Income Calculation Engine
**Goal**: Users can enter monthly work hours and additional household earnings, and the system computes gross and net income per month
**Depends on**: Phase 12 (rates and costs from settings)
**Requirements**: INC-01, INC-02, INC-03, INC-04, INC-05
**Success Criteria** (what must be TRUE):
  1. User can enter hours worked for each of the 3 rates for any month of the year, with hours defaulting to 160 when left blank
  2. User sees calculated gross income (Rate1×Time1 + Rate2×Time2 + Rate3×Time3) for each month
  3. User sees calculated net pension ((each rate×hours)×0.88 minus flat costs) for each month
  4. User can add multiple additional earnings entries (partner salary, ZUS child bonuses) per month with name and amount
**Plans**: 3 plans

Plans:
- [ ] 13-01-PLAN.md — Income data layer (models, schemas, repos, service, API, i18n)
- [ ] 13-02-PLAN.md — Income page UI (12-month grid, calculations, sidebar)
- [ ] 13-03-PLAN.md — Integration tests + human verification

### Phase 14: Expense Management
**Goal**: Users can manage recurring monthly expenses and one-time expenses via a compact Excel-style table interface with inline editing, filtering, and sorting
**Depends on**: Phase 12 (budget infrastructure/models)
**Requirements**: EXP-01, EXP-02, EXP-03, EXP-04
**Success Criteria** (what must be TRUE):
  1. User can add, edit, and delete recurring monthly expenses with name and amount
  2. User can add, edit, and delete one-time expenses with name, amount, and target month
  3. Recurring expense totals are automatically applied to every month's calculations without manual entry
**Plans**: 3 plans

Plans:
- [ ] 14-01-PLAN.md — Expense data layer (model, schemas, repo, service, API, i18n)
- [ ] 14-02-PLAN.md — Expenses page UI (compact table rows, inline edit, filtering, sorting, sidebar)
- [ ] 14-03-PLAN.md — Integration tests + human verification

### Phase 15: Year Overview Dashboard
**Goal**: Users see a 12-month financial dashboard showing income, expenses, monthly balance, and running account total
**Depends on**: Phase 12, Phase 13, Phase 14 (needs settings, income, and expenses data)
**Requirements**: YOV-01, YOV-02, YOV-03, YOV-04, YOV-05
**Success Criteria** (what must be TRUE):
  1. User sees a 12-month table with columns: Month | Monthly Expenses | Additional Expenses | +/- on Month | Account End of Month
  2. +/- on Month correctly equals: Net Pension + Additional Earnings − Recurring Expenses − One-Time Expenses
  3. Account End of Month shows running balance starting from initial bank balance in January, accumulating through December
  4. All figures recalculate automatically when any input (rates, hours, expenses, balance) changes — no manual refresh needed

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|---------------|--------|-----------|
| 12. Budget Data Foundation & Settings UI | 3/3 | Complete    | 2026-03-20 |
| 13. Income Calculation Engine | 0/? | Complete    | 2026-03-20 |
| 14. Expense Management | 3/3 | Complete    | 2026-03-20 |
| 15. Year Overview Dashboard | 1/1 | Complete    | 2026-03-20 |
| 16. Overview Month Detail | 2/2 | Complete    | 2026-03-20 |
| 17. Performance Optimization | 2/2 | Complete    | 2026-03-20 |

### Phase 16: Overview month detail - clickable months showing one-time expense breakdown

**Goal:** Users can click any month row in the year overview to expand an inline accordion detail showing one-time expense breakdown with full CRUD (add, edit, delete)
**Requirements**: OMD-01, OMD-02, OMD-03, OMD-04, OMD-05
**Depends on:** Phase 15
**Success Criteria** (what must be TRUE):
  1. User can click any month row to expand an inline detail showing one-time expenses for that month
  2. Expanded detail shows expense name, amount, and total — with inline add, edit, and delete
  3. Only one month is expanded at a time (accordion) with smooth CSS animation
  4. CRUD operations in detail use existing expense API and recalculate overview totals
**Plans:** 2 plans

Plans:
- [x] 16-01-PLAN.md — Overview API extension + accordion UI with CRUD detail
- [x] 16-02-PLAN.md — Integration tests + human verification

### Phase 17: Performance optimization - faster page loads and API responses

**Goal:** Eliminate Tailwind CDN runtime dependency with prebuilt CSS, add HTTP connection pooling in the database layer, and serve static assets with caching headers
**Requirements**: PERF-01, PERF-02, PERF-03
**Depends on:** Phase 16
**Success Criteria** (what must be TRUE):
  1. No pages load the Tailwind CDN play script — all styling comes from a prebuilt static CSS file
  2. SupabaseStore reuses httpx connections across requests (connection pooling)
  3. Static CSS file served with Cache-Control headers
  4. All existing tests continue to pass (no regressions)
**Plans:** 2 plans

Plans:
- [x] 17-01-PLAN.md — Tailwind CSS build + static file serving + connection pooling
- [x] 17-02-PLAN.md — Integration tests + human verification

---

*Roadmap updated: 2026-03-20*
