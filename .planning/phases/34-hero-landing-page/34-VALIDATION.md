---
phase: 34
slug: hero-landing-page
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-24
---

# Phase 34 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/test_go_to_market.py::TestLandingPage -x` |
| **Full suite command** | `pytest tests/test_go_to_market.py -v` |
| **Estimated runtime** | ~0.2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_go_to_market.py::TestLandingPage -x`
- **After every plan wave:** Run `pytest tests/test_go_to_market.py -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 1 second

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 34-01-01 | 01 | 1 | HERO-01 | integration | `pytest tests/test_go_to_market.py::TestLandingPage::test_landing_page_has_social_proof -x` | ✅ | ✅ green |
| 34-01-01 | 01 | 1 | HERO-02 | integration | `pytest tests/test_go_to_market.py::TestLandingPage::test_landing_page_has_og_tags -x` | ✅ | ✅ green |
| 34-01-01 | 01 | 1 | HERO-03 | integration | `pytest tests/test_go_to_market.py::TestLandingPage::test_landing_page_has_register_cta -x` | ✅ | ✅ green |
| 34-01-01 | 01 | 1 | HERO-04 | integration | `pytest tests/test_go_to_market.py::TestLandingPage::test_landing_page_has_features -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

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
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

All 4 requirements (HERO-01 through HERO-04) have automated test coverage in `tests/test_go_to_market.py`. All 7 landing page tests pass green.
