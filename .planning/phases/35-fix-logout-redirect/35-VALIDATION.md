---
phase: 35
slug: fix-logout-redirect
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-24
---

# Phase 35 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.4.3 |
| **Config file** | pyproject.toml |
| **Quick run command** | `python -m pytest tests/test_auth.py -k test_logout -x` |
| **Full suite command** | `python -m pytest tests/test_auth.py -x -v` |
| **Estimated runtime** | ~0.04 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_auth.py -k test_logout -x`
- **After every plan wave:** Run `python -m pytest tests/test_auth.py -x -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 1 second

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 35-01-01 | 01 | 1 | Logout redirects to login (POST 303) | integration | `pytest tests/test_auth.py::test_logout_post_redirects_to_login -x` | ✅ | ✅ green |
| 35-01-01 | 01 | 1 | Logout redirects to login (GET 302) | integration | `pytest tests/test_auth.py::test_logout_get_redirects_to_login -x` | ✅ | ✅ green |
| 35-01-01 | 01 | 1 | Session + refresh cookies cleared | integration | `pytest tests/test_auth.py::test_logout_clears_session_cookie -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

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
- [x] Feedback latency < 1s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-24

---

## Validation Audit 2026-03-24

| Metric | Count |
|--------|-------|
| Gaps found | 1 |
| Resolved | 1 |
| Escalated | 0 |

**Gap resolved:** `test_logout_clears_session_cookie` now asserts both `session=` and `supabase_refresh=` cookie clearing.
