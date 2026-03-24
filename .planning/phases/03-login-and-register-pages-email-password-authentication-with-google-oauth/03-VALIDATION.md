---
phase: 03
slug: login-and-register-pages-email-password-authentication-with-google-oauth
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `python -m pytest tests/test_auth.py -x --tb=short` |
| **Full suite command** | `python -m pytest tests/ -x --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_auth.py -x --tb=short`
- **After every plan wave:** Run `python -m pytest tests/ -x --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | AUTH-01 | unit+integration | `python -m pytest tests/test_auth.py -x --tb=short` | ✅ | ⬜ pending |
| 03-01-02 | 01 | 1 | AUTH-01 | integration | `python -m pytest tests/test_auth.py -x --tb=short` | ✅ | ⬜ pending |
| 03-02-01 | 02 | 2 | AUTH-02 | unit+integration | `python -m pytest tests/test_auth.py -x --tb=short` | ✅ | ⬜ pending |
| 03-02-02 | 02 | 2 | AUTH-02 | integration | `python -m pytest tests/test_auth.py -x --tb=short` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. `tests/test_auth.py` and `tests/conftest.py` already exist.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Glassmorphic UI matches Synco brand | AUTH-01 | Visual design | Visit /auth/login and /auth/register, verify dark theme, blur cards, gradient buttons |
| Google OAuth button launches flow | AUTH-01 | External service | Click "Sign in with Google" on login page, verify redirect to Google |
| Password reset email arrives | AUTH-02 | External email | Submit forgot-password form, check inbox for Supabase recovery email |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
