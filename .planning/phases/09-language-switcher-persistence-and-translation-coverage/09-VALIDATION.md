---
phase: 09
slug: language-switcher-persistence-and-translation-coverage
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-20
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for language switcher, persistence, and translation coverage.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4.3 |
| **Config file** | pyproject.toml |
| **Quick run command** | `.venv\Scripts\python.exe -m pytest tests/test_calendar_views.py -k "locale" -q` |
| **Full suite command** | `.venv\Scripts\python.exe -m pytest tests/test_calendar_views.py tests/test_auth.py -q` |
| **Estimated runtime** | ~1 second |

---

## Sampling Rate

- **After every task commit:** Run `.venv\Scripts\python.exe -m pytest tests/test_calendar_views.py -k "locale" -q`
- **After every plan wave:** Run `.venv\Scripts\python.exe -m pytest tests/test_calendar_views.py tests/test_auth.py -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | I18N-02 | integration | `.venv\Scripts\python.exe -m pytest tests/test_calendar_views.py -k "switch_locale" -q` | ✅ | ✅ green |
| 09-01-02 | 01 | 1 | I18N-03 | integration | `.venv\Scripts\python.exe -m pytest tests/test_calendar_views.py -k "locale_cookie" -q` | ✅ | ✅ green |
| 09-02-01 | 02 | 2 | I18N-06 | fixture | `grep -n "locale_reset_client\|get_page_in_locale\|assert_locale_rendered" tests/conftest.py tests/test_calendar_views.py` | ✅ | ✅ green |
| 09-02-02 | 02 | 2 | I18N-06 | integration | `.venv\Scripts\python.exe -m pytest tests/test_calendar_views.py -k "default_locale or switch_locale or locale_cookie or english_locale or query_param" -q` | ✅ | ✅ green |
| 09-02-03 | 02 | 2 | I18N-06 | regression | `.venv\Scripts\python.exe -m pytest tests/ -q` | ✅ | ✅ green |

---

## Requirement Coverage

| Requirement | Description | Tests | Status |
|-------------|-------------|-------|--------|
| I18N-02 | Switch language from nav | `test_switch_locale_from_polish_to_english` — loads `/?lang=en`, asserts English labels (Calendar, Logout, Google Sync) and `lang="en"` | ✅ COVERED |
| I18N-03 | Language persists across refresh | `test_locale_cookie_persists_across_reload` — sets English via `?lang=en`, verifies cookie `locale=en`, reloads without param, asserts English renders | ✅ COVERED |
| I18N-06 | Automated test coverage for locale | 5 dedicated integration tests: `test_default_locale_is_polish`, `test_switch_locale_from_polish_to_english`, `test_locale_cookie_persists_across_reload`, `test_english_locale_consistent_across_pages`, `test_query_param_overrides_cookie` | ✅ COVERED |

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-20

---

## Validation Audit 2026-03-20

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Reconstructed from phase artifacts (State B — no prior VALIDATION.md). All 3 requirements (I18N-02, I18N-03, I18N-06) have automated test coverage. 5 dedicated locale integration tests all pass.
