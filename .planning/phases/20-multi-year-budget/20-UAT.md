---
status: complete
phase: 20-multi-year-budget
source: [20-01-SUMMARY.md, 20-02-SUMMARY.md]
started: 2026-03-21T00:00:00Z
updated: 2026-03-21T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Year Navigation Arrow Bounds
expected: Open Budget Overview. Navigate to the earliest year with data. The left (previous year) arrow should be visually disabled — dimmed out, cursor changes to not-allowed, and clicking it does nothing. Similarly, navigate to the latest year — the right (next year) arrow should be disabled.
result: pass

### 2. Year Forward/Backward Navigation
expected: Use the year arrows to navigate between years. Each year should load its own budget overview data (different monthly figures). The year label should update accordingly.
result: pass

### 3. Carry-Forward Balance — First Year
expected: On the earliest year with budget data, the initial balance line should display the manually set initial balance amount. It should NOT show "Carried from" text — just the initial balance as configured in settings.
result: pass

### 4. Carry-Forward Balance — Later Year
expected: Navigate to any year after the first. The balance line should show "Carried from [previous year]" (or "Przeniesione z [rok]" in Polish) with the amount derived from the prior year's ending December balance. The text should be color-coded.
result: pass

### 5. Carry-Forward i18n
expected: Switch between English and Polish (if applicable). The carry-forward labels should appear in the correct language — "Carried from {year}" in English, "Przeniesione z {rok}" in Polish. "No prior year data" messages should also be translated.
result: pass

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
