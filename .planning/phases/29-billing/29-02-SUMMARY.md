---
phase: 29-billing
plan: 02
subsystem: billing
tags: [entitlements, billing-ui, i18n, plan-gating]

requires: [29-01]
provides:
  - get_current_plan and require_plan entitlement dependencies
  - get_user_plan_for_template helper for template context
  - Billing settings page with plan display and Stripe portal access
  - Plan badge in navigation bar for paid users
  - 20 billing i18n keys in both en.json and pl.json
affects: [30-saas, 33-launch]

tech-stack:
  added: []
  patterns:
    - "FastAPI dependency injection for plan entitlements (get_current_plan, require_plan)"
    - "Template-level plan context via get_user_plan_for_template helper"
    - "Stripe Customer Portal redirect for subscription management"

key-files:
  created:
    - app/billing/dependencies.py
    - app/billing/views.py
    - app/templates/billing_settings.html
  modified:
    - app/templates/base.html
    - app/locales/en.json
    - app/locales/pl.json
    - main.py

key-decisions:
  - "Entitlement check returns plan string (free/pro/family_plus) rather than boolean for flexible gating"
  - "require_plan() returns FastAPI Depends factory accepting tuple of allowed plans, raises 403 on mismatch"
  - "Billing settings page shows upgrade CTA with plan comparison for free users, manage subscription button for paid"
  - "Plan badge in nav uses green dot indicator for paid users"

patterns-established:
  - "get_current_plan dependency returns 'free' when no subscription found (graceful default)"
  - "get_user_plan_for_template(user, db) provides plan info dict for Jinja2 templates"
  - "Checkout buttons use JS fetch to POST /api/billing/checkout then redirect to Stripe URL"

requirements-completed:
  - SAS-04
  - SAS-05
  - SAS-06

duration: 6min
completed: 2026-03-23
---

# Plan 29-02: Entitlements, Billing Settings Page, and i18n

**Implemented plan-aware entitlements, billing settings UI, and full i18n support for billing features.**

## Performance

- **Duration:** 6 min
- **Tasks:** 2/2 completed
- **Files created:** 3, modified: 4

## Accomplishments
- Created get_current_plan and require_plan FastAPI dependencies for plan gating
- Added get_user_plan_for_template helper for template-level plan awareness
- Built billing settings page with current plan display, status, renewal date
- Added upgrade CTA with Pro/Family Plus plan comparison cards for free users
- Integrated Stripe Customer Portal access via manage subscription button
- Added plan badge with green dot in base.html navigation for paid users
- Added 20 billing i18n keys to both en.json and pl.json

## Task Commits

1. **Task 1: Entitlement dependencies and base.html nav** — `4def573` (feat)
2. **Task 2: Billing settings page with i18n** — `146ca3f` (feat)
