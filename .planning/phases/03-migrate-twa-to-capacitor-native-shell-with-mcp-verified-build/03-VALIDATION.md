---
phase: 03
slug: migrate-twa-to-capacitor-native-shell-with-mcp-verified-build
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), Capacitor CLI doctor (native) |
| **Config file** | pyproject.toml (pytest), capacitor.config.ts (Capacitor) |
| **Quick run command** | `pytest tests/test_pwa.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_pwa.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | CAP-01/02/03 | integration | `npx cap doctor` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | CAP-04 | file check | `Test-Path android/app/build.gradle` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | CAP-05 | CI lint | `actionlint .github/workflows/android-build.yml` | ✅ | ⬜ pending |
| 03-02-02 | 02 | 2 | CAP-06/07 | manual | Physical device install | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `capacitor.config.ts` — Capacitor config created during Plan 01 Task 1
- [ ] `www/index.html` — minimal web dir for Capacitor created during Plan 01 Task 1
- [ ] `npm install @capacitor/core @capacitor/cli @capacitor/android` — Capacitor dependencies

*Existing pytest infrastructure covers backend verification. Capacitor tooling installed during execution.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| APK installs without Chrome | CAP-01 | Requires physical device | Install APK on device with Chrome disabled |
| Fullscreen standalone launch | CAP-07 | Requires physical device | Launch app, confirm no browser URL bar |
| Offline fallback works | CAP-03 | Requires airplane mode | Enable airplane mode, launch app |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
