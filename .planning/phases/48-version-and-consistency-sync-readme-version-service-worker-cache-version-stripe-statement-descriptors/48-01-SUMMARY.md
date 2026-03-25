# Phase 48 — Plan 01 Summary: Version & Consistency Sync

## What Was Done

### Task 1: Version Sync
- `pyproject.toml`: version `4.0.0` → `5.1.0`
- `README.md`:
  - Version header: `v3.0 (shipped 2026-03-23)` → `v5.1 (shipped 2026-03-25)`
  - Test count: `331 passing across 17 test files` → `581 passing across 22 test files`
  - Milestones: added v4.0, v5.0, v5.1 entries
  - Release History table: added 3 rows (v4.0, v5.0, v5.1) before v3.0
- `public/sw.js`: cache name `dobryplan-v1` → `dobryplan-v5.1` (forces cache bust)
- `public/manifest.json`: description `"Smart household calendar & budget planner"` → `"Shared household calendar, budget planner & shopping list"` (includes shopping)

### Task 2: Stripe Statement Descriptor
- Added conditional `extra` dict in `create_checkout_session`:
  - Subscriptions: `subscription_data` with user metadata
  - One-time payments: `payment_intent_data` with `statement_descriptor: "DOBRYPLAN"`
- Passed via `**extra` to `stripe.checkout.Session.create()`

## Files Modified
- `pyproject.toml` — version bump
- `README.md` — version, test count, milestone list, release history table
- `public/sw.js` — cache name
- `public/manifest.json` — description
- `app/billing/service.py` — statement_descriptor + subscription_data

## Verification
- `5.1.0` in pyproject.toml confirmed
- `v5.1` and `v4.0` in README confirmed
- `dobryplan-v5.1` in sw.js confirmed
- `"shopping"` in manifest description confirmed
- `DOBRYPLAN` in billing service confirmed
- 581 tests passed, 12 skipped

## Commit
- `cee5b9a` feat(48-01): version sync to v5.1, SW cache bust, manifest update, Stripe statement descriptor
