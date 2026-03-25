---
phase: 36
slug: e2e-test-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 36 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | @playwright/test (Node.js) |
| **Config file** | e2e/playwright.config.ts |
| **Quick run command** | `npx playwright test --project=setup` |
| **Full suite command** | `npx playwright test` |
| **Estimated runtime** | ~30 seconds (network-bound against Railway) |

---

## Sampling Rate

- **After every task commit:** Run `npx playwright test --project=setup`
- **After every plan wave:** Run `npx playwright test`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 36-01-01 | 01 | 1 | INFRA-01 | config | `test -f e2e/playwright.config.ts` | ❌ W0 | ⬜ pending |
| 36-01-02 | 01 | 1 | INFRA-02 | e2e | `npx playwright test --project=setup` | ❌ W0 | ⬜ pending |
| 36-02-01 | 02 | 2 | INFRA-03, INFRA-04 | e2e | `npx playwright test` | ❌ W0 | ⬜ pending |
| 36-02-02 | 02 | 2 | INFRA-05 | config | `cat .github/workflows/e2e.yml` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `e2e/playwright.config.ts` — Playwright config with setup project and 3 role projects
- [ ] `e2e/auth.setup.ts` — Login all 3 accounts and save storage state
- [ ] `@playwright/test` devDependency — install via `npm install -D @playwright/test`

*Framework installation is part of plan tasks — no separate Wave 0 needed since this IS the infrastructure phase.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GitHub Actions secrets configured | INFRA-05 | Secrets stored in GitHub dashboard | Verify E2E_* secrets exist in repo Settings > Secrets |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
