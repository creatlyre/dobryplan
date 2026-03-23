# Roadmap: CalendarPlanner

## Milestones

- [x] v1.0 milestone - Phases 1-7 shipped 2026-03-19 (22/22 plans complete). Archive: .planning/milestones/v1.0-ROADMAP.md
- [x] v1.1 milestone - Phases 8-11 shipped 2026-03-20 (10/10 plans complete). Archive: .planning/milestones/v1.1-ROADMAP.md
- [x] v2.0 milestone — Budget Tracker - Phases 12-17 shipped 2026-03-20 (230 tests passing). Archive: .planning/milestones/v2.0-ROADMAP.md
- [x] v2.1 milestone — Privacy, Reminders & Multi-Year Budget - Phases 18-22 shipped 2026-03-22 (270 tests passing). Archive: .planning/milestones/v2.1-ROADMAP.md
- [x] v3.0 milestone — Dashboard, Notifications & Categories - Phases 23-27 shipped 2026-03-23 (331 tests passing). Archive: .planning/milestones/v3.0-ROADMAP.md
- [ ] v4.0 milestone — Monetization Foundation (SaaS primary + self-hosted purchase option) - Phases 28-33 planned

## Phases

<details>
<summary>🚧 v4.0 Monetization Foundation (Phases 28-33) — PLANNED</summary>

- [ ] Phase 28: Licensing and Commercial Terms Foundation (2 plans)
  Plans:
  - [ ] 28-01-PLAN.md — Commercial license terms, monetization docs, NOTICE
  - [ ] 28-02-PLAN.md — LICENSE verification, README licensing section
- [x] Phase 29: Billing, Plans, and Entitlements Core (2 plans) — completed 2026-03-23
  Plans:
  - [x] 29-01-PLAN.md — Billing data model, Stripe checkout, webhook handler
  - [x] 29-02-PLAN.md — Entitlement dependencies, billing settings page, i18n
- [x] Phase 30: SaaS Production Platform and Operations (2 plans) — completed 2026-03-23
  **Goal:** Production-ready deployment: Dockerfile, Railway config, security hardening, structured logging, Sentry, enhanced health checks
  **Requirements:** [SAS-01]
  Plans:
  - [x] 30-01-PLAN.md — Dockerfile, environment config, Railway deployment
  - [x] 30-02-PLAN.md — Security headers, CORS, rate limiting, logging, Sentry, health checks
- [ ] Phase 31: Paid Self-Hosted Distribution (2 plans)
  **Goal:** Docker Compose package with license-key verification, setup guide, upgrade path, and changelog for paid self-hosted buyers
  **Requirements:** [SHS-01, SHS-02, SHS-03, SHS-04]
  Plans:
  - [ ] 31-01-PLAN.md — License key system, Docker Compose package
  - [ ] 31-02-PLAN.md — Setup guide, upgrade docs, changelog, license tests
- [ ] Phase 32: Mobile Distribution Path (PWA + Android Wrapper)
- [ ] Phase 33: Go-to-Market, Pricing, and Launch Funnel

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

<details>
<summary>✅ v2.1 Privacy, Reminders & Multi-Year Budget (Phases 18-22) — SHIPPED 2026-03-21</summary>

- [x] Phase 18: Event Privacy (2/2 plans) — completed 2026-03-20
- [x] Phase 19: Reminder UI (1/1 plan) — completed 2026-03-20
- [x] Phase 20: Multi-Year Budget (2/2 plans) — completed 2026-03-21
- [x] Phase 21: Year-over-Year Comparison (1/1 plan) — completed 2026-03-21
- [x] Phase 22: Historical Year Import (1/1 plan) — completed 2026-03-21

</details>

<details>
<summary>✅ v3.0 Dashboard, Notifications & Categories (Phases 23-27) — SHIPPED 2026-03-23</summary>

- [x] Phase 23: Event Categories & Colors (2/2 plans) — completed 2026-03-22
- [x] Phase 24: Expense Categories & Charts (2/2 plans) — completed 2026-03-23
- [x] Phase 25: Shopping List (2/2 plans) — completed 2026-03-23
- [x] Phase 26: Notifications (3/3 plans) — completed 2026-03-23
- [x] Phase 27: Dashboard (2/2 plans) — completed 2026-03-23

</details>

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
| 23. Event Categories & Colors | v3.0 | 2/2 | Complete | 2026-03-22 |
| 24. Expense Categories & Charts | v3.0 | 2/2 | Complete | 2026-03-23 |
| 25. Shopping List | v3.0 | 2/2 | Complete | 2026-03-23 |
| 26. Notifications | v3.0 | 3/3 | Complete | 2026-03-23 |
| 27. Dashboard | v3.0 | 2/2 | Complete | 2026-03-23 |
| 28. Licensing and Commercial Terms Foundation | 2/2 | Complete    | 2026-03-23 | - |
| 29. Billing, Plans, and Entitlements Core | v4.0 | 0/2 | Planned | - |
| 30. SaaS Production Platform and Operations | v4.0 | 2/2 | Complete | 2026-03-23 |
| 31. Paid Self-Hosted Distribution | v4.0 | Complete    | 2026-03-23 | - |
| 32. Mobile Distribution Path (PWA + Android Wrapper) | v4.0 | 0/0 | Planned | - |
| 33. Go-to-Market, Pricing, and Launch Funnel | v4.0 | 0/0 | Planned | - |

---

*Roadmap updated: 2026-03-23 for v4.0 monetization planning*
