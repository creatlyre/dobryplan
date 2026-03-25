# Phase 40 Plan 01 Summary — E2E Test Gate

## What was built
Fixed all 18 failing E2E tests (6 unique failures × 3 projects) achieving 126/126 pass rate.

## Root causes identified and fixed

### 1. Calendar modal JS crash (6 failures across 3 projects)
- **Symptom**: "event entry button opens modal" test fails — clicking "+ Add Event" doesn't open the modal
- **Root cause**: `formatReminderMinutes()` was defined in base.html AFTER `{% block content %}`, but calendar.html's script called `renderReminderChips()` during init which needs it. This caused `formatReminderMinutes is not defined` error, halting script execution before event listeners were attached.
- **Fix**: Moved `formatReminderMinutes` and `pad2` function definitions to a `<script>` block before the `{% block content %}` in base.html.

### 2. Pro user subscription plan incorrect (12 failures across 3 projects)
- **Symptom**: Pro test user gets 403 on gated routes (/shopping, /budget/stats, /budget/import)
- **Root cause**: Pro test user (test2@gmail.com) had `plan: "free"` in the subscriptions table instead of `plan: "pro"`.
- **Fix**: Updated subscription record in Supabase: `UPDATE subscriptions SET plan = 'pro' WHERE user_id = 'a7c9126f-...'`.

## Artifacts
- `app/templates/base.html` — formatReminderMinutes moved before content block

## Verification
```
126 passed (1.7m)
```
All E2E tests pass across free, pro, and family-plus projects.

## Commit
- `f3dfcc7` — fix: move formatReminderMinutes before content block to fix calendar JS crash
