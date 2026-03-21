---
status: complete
phase: 21-year-over-year-comparison
source: [21-01-SUMMARY.md]
started: 2026-03-21T00:00:00Z
updated: 2026-03-21T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. YoY Comparison Card Visibility
expected: Open Budget Overview. A year-over-year comparison card should be visible between the initial balance display and the monthly table. It should be a glass-style card containing a comparison table.
result: pass

### 2. Comparison Table Rows & Data
expected: The comparison table should show 6 rows: Net Income, Additional Earnings, Recurring Expenses, One-time Expenses, Net Balance, and Final Account Balance. Each row should display the current year value, previous year value, and a delta column.
result: pass

### 3. Delta Arrows & Color Coding
expected: Delta values should show colored arrows — green ▲ when the metric improved (more income/balance or less expenses), red ▼ when it worsened. For expense rows, lower spending should be green (inverted logic). A dash (—) should appear when there's no change.
result: pass

### 4. Year Navigation Updates Comparison
expected: Navigate to a different year using the year arrows. The comparison card should update to compare the newly selected year against its previous year. The data should change accordingly.
result: pass

### 5. Comparison i18n
expected: Switch between English and Polish. All comparison labels (row names, column headers) should appear in the correct language.
result: pass

### 6. Graceful Degradation
expected: If you navigate to the earliest year (where no prior year data exists), the comparison card should still render without errors. It may show zeros or dashes for the previous year column.
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
