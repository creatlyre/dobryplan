---
phase: 05-natural-language-input
verified: 2026-03-19T11:52:23.4001957Z
status: gaps_found
score: 2/5 must-haves verified
gaps:
  - truth: "User can type a natural language phrase (for example dentist Thursday 2pm) and the app parses it into a structured event"
    status: failed
    reason: "Core sample phrase is not parsed; parser returns No date found in input for weekday-only phrase without next/this/last. NLP test suite also has multiple failures."
    artifacts:
      - path: "app/events/nlp.py"
        issue: "Relative-day parser only matches next|this|last + weekday and misses plain weekday phrases like Thursday."
      - path: "tests/test_nlp.py"
        issue: "Phase NLP tests fail (6 failures) including recurrence and past-date checks."
    missing:
      - "Support plain weekday anchors (Thursday, Friday) in parse logic"
      - "Fix title/date extraction defects causing malformed titles and missing past-date errors"
      - "Make recurrence parsing work when phrase has recurrence without explicit date anchor"
  - truth: "Ambiguous month/day parsing asks user to clarify year (Did you mean 2026 or 2027?)"
    status: failed
    reason: "Implementation auto-picks nearest future year with confidence 0.85 but does not provide clarification prompt flow."
    artifacts:
      - path: "app/events/nlp.py"
        issue: "Month/day parser auto-rolls to next year with no ambiguity prompt output."
      - path: "app/templates/calendar.html"
        issue: "No year-disambiguation UI state for parse review."
    missing:
      - "Return explicit ambiguity metadata when month/day lacks year"
      - "Add UI confirmation path for year choice before save"
  - truth: "All parser logic respects user's timezone context"
    status: failed
    reason: "Parse endpoint hardcodes UTC timezone instead of using user/session timezone."
    artifacts:
      - path: "app/events/routes.py"
        issue: "Route sets timezone = UTC before invoking NLPService.parse."
    missing:
      - "Read timezone from user profile/session and pass it into NLPService"
      - "Add API tests validating non-UTC user timezone propagation"
human_verification:
  - test: "Quick Add visual and responsive behavior"
    expected: "Desktop uses centered dialog, mobile uses full-screen modal; transitions between text, loading, review, and fallback are understandable"
    why_human: "Automated checks confirm markup and handlers, but not visual layout quality/usability"
  - test: "Screen reader and keyboard a11y flow"
    expected: "Focus trap is intuitive, live-region announcements are understandable, and error/fix wording is clear for assistive tech users"
    why_human: "Programmatic checks cannot fully validate real screen reader announcements and interaction quality"
---

# Phase 05: Natural Language Input Verification Report

Phase Goal: Users can quickly add events by typing natural language descriptions (for example dentist Thursday 2pm).
Verified: 2026-03-19T11:52:23.4001957Z
Status: gaps_found
Re-verification: No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | User can parse quick-add natural language sample phrase into structured event | x FAILED | Direct runtime check: NLPService.parse("dentist Thursday 2pm") returned errors ["No date found in input"]. Relative parser in app/events/nlp.py only handles next/this/last + weekday. |
| 2 | Parsed event is displayed for user confirmation before saving | VERIFIED | app/templates/calendar.html calls /api/events/parse and transitions to review via populateReview + showPhase('review'). Review fields exist in quick_add_modal. |
| 3 | User can correct parsed fields before committing | VERIFIED | Editable review inputs and save actions exist (qa-parsed-title/start/end/repeat/count/until, save buttons) and are wired in calendar JS. |
| 4 | Ambiguous month/day parsing supports year clarification | x FAILED | app/events/nlp.py auto-selects current/next year in _parse_month_day with confidence 0.85; no user clarification prompt metadata or UI branch found. |
| 5 | Relative dates parse for tomorrow, in 3 days, next Friday | PARTIAL/FAILED | Runtime checks: tomorrow and next Friday parse, but in 3 days produced 03:00 due numeric token capture as hour; indicates incorrect interpretation of phrase intent. |

Score: 2/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| app/events/nlp.py | NLP parsing core for phase goal | VERIFIED (with gaps) | Substantive implementation exists, but misses core phrase and has failing tests tied to behavior. |
| app/events/routes.py | Parse endpoint wiring to NLP service | VERIFIED (with gap) | /api/events/parse exists and returns parse payload, but timezone is hardcoded UTC. |
| app/templates/calendar.html | Quick-add modal orchestration parse/review/save | VERIFIED | Modal state machine and endpoint wiring are implemented. |
| app/templates/partials/quick_add_modal.html | Review/edit/error/a11y markup | VERIFIED | Modal/review/error/live-region controls exist. |
| app/templates/partials/fallback_form.html | Manual fallback entry form | VERIFIED | Fallback form exists and is wired from calendar page after repeated parse failures. |
| tests/test_nlp.py | NLP behavior validation | FAILED | Running tests/test_nlp.py produced 6 failures (title extraction, past-date behavior, recurrence parsing). |
| tests/test_events_api.py | Parse endpoint/API regression coverage | VERIFIED | Parse endpoint tests pass in combined run except failures were isolated to NLP tests. |
| tests/test_calendar_views.py | Quick-add UI integration assertions | VERIFIED | Quick-add route/markup/orchestration tests pass. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| app/templates/calendar.html | /api/events/parse | fetch POST with text + context_date | WIRED | fetch call and success/error handling present. |
| app/events/routes.py | app/events/nlp.py | parse_event invokes NLPService.parse | WIRED | Route instantiates NLPService and returns parsed response model. |
| app/templates/calendar.html | /api/events | saveEvent and fallback save POST | WIRED | Both review save and fallback save post structured payload to event API. |
| app/events/routes.py | user timezone context | parse_event timezone selection | NOT_WIRED | Hardcoded timezone = UTC instead of profile/session timezone. |
| app/events/nlp.py | sample phrase dentist Thursday 2pm | relative-day parsing path | NOT_WIRED | No plain weekday pattern support. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| NLP-01 | 05-01-PLAN.md | Parse natural language description into structured event for review | BLOCKED | Sample phrase and multiple NLP tests fail; parser misses plain weekday phrase and recurrence/date edge cases. |
| NLP-02 | 05-01/05-02/05-03 | Parsed event shown for confirmation before saving | SATISFIED | Review phase and parse-to-review transition are implemented in calendar + modal templates. |
| NLP-03 | 05-01/05-02/05-03 | User can correct parsed fields before saving | SATISFIED | Review inputs and fallback manual form are editable and save through existing event API. |

Orphaned requirements check: None found for Phase 05. Plans reference NLP-01, NLP-02, NLP-03 and REQUIREMENTS mapping includes those IDs.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| app/templates/calendar.html | 83 | return null | INFO | Normal null return for no-repeat RRULE helper; not a stub. |

No blocker TODO/FIXME/placeholder patterns found in phase key files.

### Human Verification Required

### 1. Quick Add Visual Responsiveness

Test: Open Quick Add on desktop and mobile widths, run text-entry to review to fallback to save flow.
Expected: Desktop dialog and mobile full-screen behavior are visually clear and usable.
Why human: Automated checks validate structure and JS wiring, not visual UX quality.

### 2. Accessibility Usability Audit

Test: Navigate Quick Add fully via keyboard and screen reader (focus trap, errors, review announcements, fallback form).
Expected: Assistive technology announcements are clear and flow is understandable without visual cues.
Why human: Requires real assistive-tech behavior validation.

### Gaps Summary

Phase 05 delivers substantial UI wiring and parse endpoint integration, but the goal is not yet achieved because core NLP parsing behavior remains unreliable for the representative phrase and related edge cases. The largest blocker is NLP-01: parser behavior does not consistently support the intended user input contract. Additional functional gap exists for ambiguity-year clarification and timezone propagation from authenticated user context.

---

Verified: 2026-03-19T11:52:23.4001957Z
Verifier: Claude (gsd-verifier)
