# Roadmap: CalendarPlanner

## Milestones

- [x] v1.0 milestone - Phases 1-7 shipped 2026-03-19 (22/22 plans complete). Archive: .planning/milestones/v1.0-ROADMAP.md
- [x] v1.1 milestone - Phases 8-11 shipped 2026-03-20 (10/10 plans complete). Archive: .planning/milestones/v1.1-ROADMAP.md
- [x] v2.0 milestone — Budget Tracker - Phases 12-17 shipped 2026-03-20 (230 tests passing). Archive: .planning/milestones/v2.0-ROADMAP.md
- [x] v2.1 milestone — Privacy, Reminders & Multi-Year Budget - Phases 18-22 shipped 2026-03-22 (270 tests passing). Archive: .planning/milestones/v2.1-ROADMAP.md
- [ ] v3.0 milestone — Dashboard, Notifications & Categories - Phases 23-27

## Phases

<details>
<summary>✅ v2.0 Budget Tracker (Phases 12-17) — SHIPPED 2026-03-20</summary>

- [x] Phase 12: Budget Data Foundation & Settings UI (3/3 plans) — completed 2026-03-20
- [x] Phase 13: Income Calculation Engine (3/3 plans) — completed 2026-03-20
- [x] Phase 14: Expense Management (3/3 plans) — completed 2026-03-20
- [x] Phase 15: Year Overview Dashboard (1/1 plan) — completed 2026-03-20
- [x] Phase 16: Overview Month Detail (2/2 plans) — completed 2026-03-20
- [x] Phase 17: Performance Optimization (2/2 plans) — completed 2026-03-20

</details>

<details>
<summary>✅ v2.1 Privacy, Reminders & Multi-Year Budget (Phases 18-22) — SHIPPED 2026-03-21</summary>

- [x] Phase 18: Event Privacy (2/2 plans) — completed 2026-03-20
- [x] Phase 19: Reminder UI (1/1 plan) — completed 2026-03-20
- [x] Phase 20: Multi-Year Budget (2/2 plans) — completed 2026-03-21
- [x] Phase 21: Year-over-Year Comparison (1/1 plan) — completed 2026-03-21
- [x] Phase 22: Historical Year Import (1/1 plan) — completed 2026-03-21

</details>

### v3.0 Dashboard, Notifications & Categories (Phases 23-27)

- [x] **Phase 23: Event Categories & Colors** — Preset + custom categories with curated colors, color-coded calendar grid, category filtering
 (completed 2026-03-22)
  **Plans:** 2 plans
  Plans:
  - [ ] 23-01-PLAN.md — Backend foundation: DB migration, models, category CRUD API, event category_id integration
  - [ ] 23-02-PLAN.md — Frontend: category selector in forms, color-coded grid/day view, category filter bar
- [x] **Phase 24: Expense Categories & Charts** — Expense categorization, category selector in forms, pie/bar chart spending breakdown
 (completed 2026-03-23)
  **Plans:** 2 plans
  Plans:
  - [ ] 24-01-PLAN.md — Backend: DB migration, models, expense category CRUD API, category_id integration, stats breakdown endpoint
  - [ ] 24-02-PLAN.md — Frontend: category selector in forms, category display/filter in expense list, pie/bar charts on stats page
- [x] **Phase 25: Shopping List** — Shared household shopping list with add/delete/edit, multi-item paste, Biedronka store-section auto-grouping
  **Plans:** 2 plans
  Plans:
  - [x] 25-01-PLAN.md — Backend: DB migration, models, keyword JSON, repository, service with auto-categorization, API routes
  - [x] 25-02-PLAN.md — Frontend: shopping view, template with section-grouped display, nav links, i18n, tests
- [x] **Phase 26: Notifications** — In-app notification feed with bell badge, partner change alerts, email toggle, event reminders
  **Plans:** 3 plans
  Plans:
  - [x] 26-01-PLAN.md — Backend foundation: DB migration, models, notification repository, service, API routes
  - [x] 26-02-PLAN.md — Service hooks in event/expense/income, SMTP email alerts, reminder notification check, i18n
  - [x] 26-03-PLAN.md — Frontend: bell icon with unread badge, notification dropdown, mark-read/dismiss actions, email toggle
- [x] **Phase 27: Dashboard** — Home page with today's events, 7-day preview, budget snapshot, quick-add buttons

## Phase Details

### Phase 23: Event Categories & Colors
**Goal**: Users can categorize events and see color-coded indicators on the calendar grid
**Depends on**: Nothing (foundational for v3.0)
**Requirements**: ECAT-01, ECAT-02, ECAT-03, ECAT-04, ECAT-05
**Success Criteria** (what must be TRUE):
  1. User can assign a category (Work, Personal, Health, Errands, Social) when creating or editing an event
  2. User can create a custom category with a name and color from a curated palette
  3. Calendar month grid shows color-coded indicators (dot or border) for each event's category
  4. User can filter calendar view to show only events from selected categories
  5. Category selector appears in both event create and edit modal forms
**Plans**: 2 plans (23-01, 23-02)

### Phase 24: Expense Categories & Charts
**Goal**: Users can categorize expenses and see spending breakdowns by category
**Depends on**: Phase 23 (category pattern established)
**Requirements**: XCAT-01, XCAT-02, XCAT-03, XCAT-04, XCAT-05
**Success Criteria** (what must be TRUE):
  1. User can assign an expense to a preset category (Groceries, Rent, Utilities, Transport, Entertainment, Health, Education, Other)
  2. User can create custom expense categories
  3. Budget stats page shows pie/bar chart of spending grouped by category
  4. User can filter or group the expense list by category
  5. Category selector appears in both recurring and one-time expense forms
**Plans**: 2 plans (24-01, 24-02)

### Phase 25: Shopping List
**Goal**: Both household users share a common shopping list with Biedronka store-section auto-grouping for route-optimized shopping
**Depends on**: Nothing (independent feature)
**Requirements**: SHOP-01, SHOP-02, SHOP-04, SHOP-05
**Success Criteria** (what must be TRUE):
  1. User can add individual items to the shopping list
  2. User can delete and edit items on the shopping list
  3. Both household users see and share the same shopping list
  4. User can paste a comma/newline-separated string to add multiple items at once
  5. Items are auto-categorized into Biedronka store sections via keyword matching
**Plans**: 2 plans (25-01, 25-02)

### Phase 26: Notifications
**Goal**: Users receive in-app and optional email alerts for partner activity and event reminders
**Depends on**: Phase 23, Phase 24 (hooks into event + expense CRUD)
**Requirements**: NOTIF-01, NOTIF-02, NOTIF-03, NOTIF-04, NOTIF-05, NOTIF-06, NOTIF-07, NOTIF-08
**Success Criteria** (what must be TRUE):
  1. Bell icon in navigation shows unread notification count badge
  2. Notification feed displays partner's event and expense/income changes
  3. User can mark individual notifications as read or dismiss, and mark all as read
  4. Optional email alerts sent for partner's event changes (user preference toggle)
  5. Event reminder notifications trigger at configured reminder times before event start
**Plans**: TBD

### Phase 27: Dashboard
**Goal**: Users land on a unified home page summarizing today's schedule and finances
**Depends on**: Phase 23, Phase 24 (categories for color coding and budget snapshot)
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04
**Success Criteria** (what must be TRUE):
  1. Home page shows today's events color-coded by their assigned category
  2. Home page displays a compact 7-day upcoming events preview
  3. Budget snapshot shows current month balance, top spending categories, and income vs expenses
  4. Quick-add buttons let user create events and expenses directly from the home page
**Plans**: 2 plans
  Plans:
  - [x] 27-01-PLAN.md — Dashboard service, route, template with all 4 sections, nav updates, i18n
  - [x] 27-02-PLAN.md — Dashboard tests and template polish, edge cases, empty states

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|---------------|--------|----------|
| 12. Budget Data Foundation & Settings UI | v2.0 | 3/3 | Complete | 2026-03-20 |
| 13. Income Calculation Engine | v2.0 | 3/3 | Complete | 2026-03-20 |
| 14. Expense Management | v2.0 | 3/3 | Complete | 2026-03-20 |
| 15. Year Overview Dashboard | v2.0 | 1/1 | Complete | 2026-03-20 |
| 16. Overview Month Detail | v2.0 | 2/2 | Complete | 2026-03-20 |
| 17. Performance Optimization | v2.0 | 2/2 | Complete | 2026-03-20 |
| 18. Event Privacy | v2.1 | 2/2 | Complete | 2026-03-20 |
| 19. Reminder UI | v2.1 | 1/1 | Complete | 2026-03-20 |
| 20. Multi-Year Budget | v2.1 | 2/2 | Complete | 2026-03-21 |
| 21. Year-over-Year Comparison | v2.1 | 1/1 | Complete | 2026-03-21 |
| 22. Historical Year Import | v2.1 | 1/1 | Complete | 2026-03-21 |
| 23. Event Categories & Colors | 2/2 | Complete   | 2026-03-22 | - |
| 24. Expense Categories & Charts | 2/2 | Complete    | 2026-03-23 | - |
| 25. Shopping List | v3.0 | 2/2 | Complete | 2026-03-23 |
| 26. Notifications | v3.0 | 3/3 | Complete | 2026-03-23 |
| 27. Dashboard | v3.0 | 2/2 | Complete | 2026-03-23 |

---

*Roadmap updated: 2026-03-22 after v3.0 milestone roadmap created*
