---
phase: 20
slug: multi-year-budget
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-21
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `python -m pytest tests/test_overview.py::TestMultiYearCarryForward tests/test_overview.py::TestRecurringExpensesMultiYear -x -q` |
| **Full suite command** | `python -m pytest tests/test_overview.py -x -q` |
| **Estimated runtime** | ~0.3 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 1 second

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 20-01-T1 | 01 | 1 | BUD-01 | integration | `pytest tests/test_overview.py::TestMultiYearCarryForward::test_year_bounds_with_data -x` | ✅ | ✅ green |
| 20-01-T1 | 01 | 1 | BUD-01 | integration | `pytest tests/test_overview.py::TestMultiYearCarryForward::test_year_bounds_no_data -x` | ✅ | ✅ green |
| 20-01-T1 | 01 | 1 | BUD-01 | integration | `pytest tests/test_overview.py::TestMultiYearCarryForward::test_api_response_includes_carry_forward_and_bounds -x` | ✅ | ✅ green |
| 20-01-T1 | 01 | 1 | BUD-02 | integration | `pytest tests/test_overview.py::TestMultiYearCarryForward::test_first_year_uses_initial_balance -x` | ✅ | ✅ green |
| 20-01-T1 | 01 | 1 | BUD-02 | integration | `pytest tests/test_overview.py::TestMultiYearCarryForward::test_carry_forward_from_prior_year -x` | ✅ | ✅ green |
| 20-01-T1 | 01 | 1 | BUD-02 | integration | `pytest tests/test_overview.py::TestMultiYearCarryForward::test_no_prior_year_data_starts_from_zero -x` | ✅ | ✅ green |
| 20-01-T1 | 01 | 1 | BUD-02 | integration | `pytest tests/test_overview.py::TestMultiYearCarryForward::test_empty_year_returns_12_months -x` | ✅ | ✅ green |
| 20-01-T2 | 01 | 1 | BUD-03 | integration | `pytest tests/test_overview.py::TestRecurringExpensesMultiYear::test_recurring_expense_shows_in_different_year -x` | ✅ | ✅ green |
| 20-02-T1 | 02 | 2 | BUD-01 | static | `grep "budget.overview_carried_from" app/locales/en.json app/locales/pl.json` | ✅ | ✅ green |
| 20-02-T2 | 02 | 2 | BUD-01 | static | `grep "carry-forward-line\|updateYearNav\|renderCarryForward\|yearBounds" app/templates/budget_overview.html` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Year nav buttons gray out at bounds | BUD-01 | JS disabled state requires browser rendering | Navigate to earliest year → verify ← button is grayed (opacity 0.3). Navigate to latest+1 → verify → button is grayed. |
| Carry-forward line displays correct type | BUD-02 | Dynamic innerHTML rendering requires browser | Load first data year → see "Initial Balance: X". Load year after data → see "Carried from {year}: ±X" with green/red color. Load year after gap → see "No prior year data" message. |
| Empty year shows zero-filled 12-month table | BUD-02 | Visual layout verification | Navigate to a year with no data → verify 12-month table renders with zeros, no errors or broken layout. |

*3 manual-only items — all are frontend rendering verifications not coverable by pytest.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 1s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-21

---

## Validation Audit 2026-03-21

| Metric | Count |
|--------|-------|
| Requirements covered | 3 (BUD-01, BUD-02, BUD-03) |
| Automated tests | 8 (all green) |
| Static verifications | 2 (grep-based) |
| Manual-only | 3 (frontend rendering) |
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
