---
phase: 39
slug: billing-stripe-error-resilience-e2e
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-03-25
---

# Phase 39 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Playwright (`@playwright/test`) |
| **Config file** | `e2e/playwright.config.ts` |
| **Quick run command** | `npx playwright test --config=e2e/playwright.config.ts e2e/tests/test_billing.spec.ts e2e/tests/test_errors.spec.ts --reporter=line --retries=0` |
| **Full suite command** | `npx playwright test --config=e2e/playwright.config.ts --reporter=line` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick command (billing + errors specs)
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 39-01-01 | 01 | 1 | BILL-E2E-01, BILL-E2E-02, BILL-E2E-03, BILL-E2E-04, BILL-E2E-05 | e2e | `npx playwright test --config=e2e/playwright.config.ts e2e/tests/test_billing.spec.ts --reporter=line --retries=0` | ❌ W0 | ⬜ pending |
| 39-02-01 | 02 | 1 | ERR-E2E-01, ERR-E2E-02, ERR-E2E-03 | e2e | `npx playwright test --config=e2e/playwright.config.ts e2e/tests/test_errors.spec.ts --reporter=line --retries=0` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `e2e/tests/test_billing.spec.ts` — Pricing page rendering + checkout API + billing settings + portal API
- [ ] `e2e/tests/test_errors.spec.ts` — Auth redirects + API error responses

*Wave 0 tasks create these files directly as part of plan execution.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
