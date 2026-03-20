# Roadmap: CalendarPlanner

## Milestones

- [x] v1.0 milestone - Phases 1-7 shipped 2026-03-19 (22/22 plans complete). Archive: .planning/milestones/v1.0-ROADMAP.md
- [x] v1.1 milestone - Phases 8-11 shipped 2026-03-20 (10/10 plans complete). Archive: .planning/milestones/v1.1-ROADMAP.md
- [x] v2.0 milestone — Budget Tracker - Phases 12-17 shipped 2026-03-20 (230 tests passing). Archive: .planning/milestones/v2.0-ROADMAP.md
- [ ] v2.1 milestone — Privacy, Reminders & Multi-Year Budget - Phases 18-21 (11 requirements, 4 phases)

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

### v2.1 Privacy, Reminders & Multi-Year Budget

- [ ] **Phase 18: Event Privacy** - Validate & harden visibility toggle, filtering, sync retraction, and lock icon
- [ ] **Phase 19: Reminder UI** - Wire reminder controls to existing backend in event forms
- [ ] **Phase 20: Multi-Year Budget** - Fix data integrity (carry-forward, year-scoping) and enable year navigation
- [ ] **Phase 21: Year-over-Year Comparison** - Side-by-side annual totals with delta indicators

## Phase Details

### Phase 18: Event Privacy
**Goal**: Users can control event visibility — private events are invisible to partner across web and Google Calendar
**Depends on**: Nothing (independent feature, backend ~90% complete)
**Requirements**: VIS-01, VIS-02, VIS-03, VIS-04
**Success Criteria** (what must be TRUE):
  1. User can toggle event visibility between shared and private in the event creation and edit forms
  2. Private events are completely invisible to partner on day view, month grid, and API responses
  3. Private events show a lock icon to the owner on the calendar grid
  4. Changing an event from shared to private deletes it from partner's Google Calendar
**Plans:** 1/2 plans executed

Plans:
- [ ] 18-01-PLAN.md — UI: Lock icons & event form visibility dropdown
- [ ] 18-02-PLAN.md — Sync retraction & privacy hardening

### Phase 19: Reminder UI
**Goal**: Users can configure event reminders through the event form, with changes synced to Google Calendar
**Depends on**: Phase 18 (both touch event form; privacy validates form infrastructure first)
**Requirements**: REM-01, REM-02, REM-03, REM-04
**Success Criteria** (what must be TRUE):
  1. User can enable/disable reminders via a toggle with editable defaults (30 min + 2 days before)
  2. User can add and remove custom reminders (up to 5) in the event form
  3. Event form shows helper text explaining reminders sync to Google Calendar
  4. Configured reminders sync to Google Calendar and trigger notifications on the user's phone
**Plans**: TBD

### Phase 20: Multi-Year Budget
**Goal**: Users can browse budget data for any past year in the overview dashboard
**Depends on**: Nothing (independent from event pipeline)
**Requirements**: BUD-01, BUD-06
**Success Criteria** (what must be TRUE):
  1. User can navigate to any past year's budget overview using year arrows
  2. Years with no budget data show a graceful empty state, not errors or misleading zeros
  3. Past year data displays correctly in the existing overview layout
**Plans**: TBD

### Phase 21: Year-over-Year Comparison
**Goal**: Users can compare budget performance across years at a glance
**Depends on**: Phase 20 (multi-year navigation must work before comparison)
**Requirements**: BUD-04
**Success Criteria** (what must be TRUE):
  1. User can view side-by-side annual totals (income, expenses, balance) for selected year vs previous year
  2. Comparison handles years with partial or no data gracefully
  3. Summary is accessible from the budget overview page
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|---------------|--------|----------|
| 12. Budget Data Foundation & Settings UI | v2.0 | 3/3 | Complete | 2026-03-20 |
| 13. Income Calculation Engine | v2.0 | 3/3 | Complete | 2026-03-20 |
| 14. Expense Management | v2.0 | 3/3 | Complete | 2026-03-20 |
| 15. Year Overview Dashboard | v2.0 | 1/1 | Complete | 2026-03-20 |
| 16. Overview Month Detail | v2.0 | 2/2 | Complete | 2026-03-20 |
| 17. Performance Optimization | v2.0 | 2/2 | Complete | 2026-03-20 |
| 18. Event Privacy | 1/2 | In Progress|  | - |
| 19. Reminder UI | v2.1 | 0/? | Not started | - |
| 20. Multi-Year Budget | v2.1 | 0/? | Not started | - |
| 21. Year-over-Year Comparison | v2.1 | 0/? | Not started | - |

---

*Roadmap updated: 2026-03-20*
