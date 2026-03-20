# Roadmap: CalendarPlanner

## Milestones

- [x] v1.0 milestone - Phases 1-7 shipped 2026-03-19 (22/22 plans complete). Archive: .planning/milestones/v1.0-ROADMAP.md
- [ ] v1.1 milestone - Localization and language switching (Polish default, English option)

## Current Milestone (v1.1)

### Phase 8: Localization foundation and Polish default

**Goal:** Introduce i18n foundations and convert all current user-facing app copy to localization keys with Polish as the default locale.
**Requirements:** I18N-01, I18N-04, I18N-05
**Depends on:** Phase 7
**Plans:** 3 plans
**Status:** ✅ COMPLETE (2a4dd7c)
**Success criteria:**
1. Calendar, auth, event forms, quick-add modals, and sync surfaces render Polish copy by default for first-time and signed-in users.
2. User-facing API error/validation messages used by UI flows are available in Polish via localization resources.
3. Locale-aware date/time rendering uses Polish formatting when locale is `pl`.

Plans:
- [x] 08-01-PLAN.md - Add i18n architecture, locale resources, and Polish default resolution
- [x] 08-02-PLAN.md - Convert templates/components/partials and API-facing copy to translation keys
- [x] 08-03-PLAN.md - Locale-aware date/time formatting and regression verification for Polish defaults

### Phase 9: Language switcher, persistence, and translation coverage

**Goal:** Provide a user-accessible Polish/English language switcher with persisted preference and complete translation behavior verification.
**Requirements:** I18N-02, I18N-03, I18N-06
**Depends on:** Phase 8
**Plans:** 2 plans
**Status:** ✅ COMPLETE (553369f)
**Success criteria:**
1. User can switch between Polish and English from app navigation in authenticated and unauthenticated flows.
2. Selected language persists across refresh and session restart.
3. Automated tests verify default Polish, runtime switching, and key bilingual render paths.

Plans:
- [x] 09-01-PLAN.md - Add language switcher UI and request/session persistence mechanics (Wave 1) — Complete
- [x] 09-02-PLAN.md - Expand integration and view tests for default locale and switch behavior (Wave 2) — Complete

### Phase 10: Verify parser works with Polish language after localization

**Goal:** Ensure NLP and OCR event parsing supports Polish language input (including diacritics) with parity to existing English parsing flows.
**Requirements**: I18N-07
**Depends on:** Phase 8, Phase 9
**Plans:** 2/2 plans complete

Plans:
- [x] 10-01-PLAN.md - Add locale-aware NLP/OCR parsing contracts for Polish text and diacritics — Complete
- [x] 10-02-PLAN.md - Add Polish parser/OCR verification tests and regression gate — Complete

### Phase 11: Fast day-click manual event entry with title+start time (end defaults to +1h), and Google Calendar reminder payload defaults/overrides with UI and sync test coverage

**Goal:** Enable rapid day-click event creation (title + time only, end auto-set to start + 1h) and ensure synced events include reminder configurations that trigger Google Calendar notifications on user devices.
**Requirements**: TBD
**Depends on:** Phase 10
**Plans:** 3/3 plans complete
**Status:** 📋 Planned

Plans:
- [ ] 11-01-PLAN.md — Fast day-click manual entry UI with form prefill, date locking, and auto-calculated end-time (Wave 1)
- [ ] 11-02-PLAN.md — Event model reminder support (backward-compatible), schema updates, and Google sync payload generation (Wave 2)
- [ ] 11-03-PLAN.md — End-to-end integration tests (day-click → sync → Google) and regression verification (Wave 3)

---

*Roadmap updated for v1.1 on 2026-03-20*
*Phase 8: ✅ Complete and committed (2a4dd7c)*
*Phase 9: ✅ Complete and committed (553369f) — 117/117 tests passing*
*Phase 10: ✅ Planned (ready for execution)*
*Phase 11: 📋 Planned (3 plans created, ready for execution) — `/gsd-execute-phase 11`*
*Next step: Execute Phase 10 or Phase 11*
