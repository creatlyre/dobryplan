# Phase 5: Natural Language Input - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Add natural-language event entry so users can type text (for example, "dentist Thursday 2pm"), review parsed fields, correct them, and then save through the existing event flow. This phase clarifies HOW this works in UX and acceptance behavior; it does not add new capabilities beyond natural-language parse -> review -> save.

</domain>

<decisions>
## Implementation Decisions

### Quick-add entry UX
- Entry starts from a primary "Quick Add" button near the Event Editor title.
- Quick-add runs in a modal flow.
- Submission is button-only across devices.
- On open, parsing context should use the currently selected calendar day.
- After parse, editable review stays inside the same modal.
- Original text is preserved as a collapsed read-only summary row during review.
- One submission creates one event only in v1.
- Cancel/close discards draft.

### Ambiguity handling UX
- For month/day phrases without year, auto-pick nearest future date and show a note (small footer note).
- For date-without-time, prefill 09:00 local and mark as editable.
- Conflicting date/time hints block save and require clarification.
- Past-date parse attempts show error with quick-fix actions (next occurrence or edit date).
- Do not show timezone text in prompts.
- Recurrence phrases should be parsed and mapped to repeat controls for confirmation.
- Parse failures should show 2-3 example phrases and keep user text editable.

### Review form behavior
- Reuse current Event Editor field layout in review mode, with parsed-value highlighting.
- Emphasize date/time and recurrence first, then title/description.
- Default duration is 60 minutes if end is not explicit.
- Actions include "Save event" and "Save and add another".
- Save is blocked until required fields are valid.
- Recurrence detection preselects repeat controls and derived count/until when available.
- Show full original text during review.
- On mobile, use full-screen modal (desktop uses dialog modal).

### Parsing acceptance rules
- Must support: explicit date+time, relative day phrases, week-relative phrases, recurrence phrases, and month/day without year.
- Reject with guidance: past-only dates without override, conflicting date/time statements, and phrases with no date anchor.
- Numeric date default is fixed DD/MM/YYYY.
- For ambiguous numeric dates under fixed DD/MM mode, always apply DD/MM directly (no confirmation prompt).
- If parse fails twice, offer manual-form fallback carrying parsed hints.
- Recurrence NLP scope in v1 is common patterns only (daily/weekly/monthly/yearly and every N weeks).
- Year clarification (when needed) occurs before entering review.

### Post-save flow
- Default save closes modal and refreshes calendar/day panels.
- "Save and add another" keeps modal open and returns to a fresh text-entry state.
- Show non-blocking toast on success.
- If API save fails, keep all edited fields in modal and show inline error.

### Error message style
- Tone is plain/direct.
- Structure is "what failed + one fix suggestion".
- Show errors inline near text input plus a short top summary line.
- Rotate 2-3 examples in parse-failure guidance.
- Date examples should always use DD/MM/YYYY.
- Show short user-visible error code under the message.
- Repeated parse failures should push "Switch to manual form" as primary CTA.
- Error remains visible until user edits text or dismisses.

### Manual fallback details
- On manual fallback, prefill title, date, time, description raw text, and recurrence guess (when available).
- Uncertain prefilled fields are highlighted in yellow with "Check this" label.
- Fallback stays inside modal.
- Original NL text remains visible as reference.
- Recurrence guess requires explicit user confirmation before save.
- If no trustworthy date exists, user must choose date manually.
- If time confidence is low, prefill 09:00 and mark for review.
- Closing fallback discards draft.

### Keyboard and accessibility behavior
- Modal opens with focus in NL input field.
- Escape closes modal except while save request is in progress.
- Modal uses strict focus trap.
- Parse success/failure status is announced via live region for screen readers.

### Claude's Discretion
- Exact visual styling, spacing, and component-level animation details.
- Exact copy wording for toasts/messages as long as tone and structure constraints are preserved.
- Internal confidence scoring thresholds and parser heuristics, provided behavior contracts above are satisfied.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and success criteria
- `.planning/ROADMAP.md` - Phase 5 boundary, success criteria, and phase-specific pitfalls.
- `.planning/REQUIREMENTS.md` - NLP-01, NLP-02, NLP-03 requirement contracts.
- `.planning/PROJECT.md` - Product scope constraints (two-user shared calendar and v1 boundaries).

### Existing implementation constraints
- `app/templates/calendar.html` - Existing calendar page layout, Event Editor placement, client-side CRUD flow, and panel refresh behavior.
- `app/templates/partials/event_form.html` - Current event form field structure (title/description/start/end/repeat inputs) to reuse for review/fallback mapping.
- `app/events/schemas.py` - Event payload fields and validation contract used by save flow.
- `app/events/routes.py` - Event API endpoints and error handling behavior to align quick-add save path.
- `app/events/service.py` - Event validation semantics (start/end rules, recurrence validation hooks) that review/fallback must satisfy before save.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/templates/partials/event_form.html`: Existing editable event fields are the base shape for parsed review and fallback editing.
- `app/templates/calendar.html`: Existing Event Editor card and page script can host the Quick Add trigger and refresh integration.

### Established Patterns
- Event create/update currently call `/api/events` or `/api/events/{id}` from browser JS and then refresh month/day panels.
- Event payload uses UTC ISO datetimes plus timezone string and optional RRULE.
- Form save errors currently surface via simple response checks; quick-add can extend this pattern with richer inline errors while keeping API contract unchanged.

### Integration Points
- Quick-add parse/review flow should connect into existing event submission path used by calendar page JS.
- Parsed recurrence output must map directly to existing repeat controls and backend RRULE validation path.
- Post-save behavior should continue using existing month/day panel reload flow.

</code_context>

<specifics>
## Specific Ideas

- Keep quick-add mobile-friendly through button-first interaction while preserving modal UX.
- Keep language deterministic and practical; avoid silent guessing except explicit fixed DD/MM interpretation.
- Use visible confidence cues in fallback (yellow fields) to direct user corrections quickly.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 05-natural-language-input*
*Context gathered: 2026-03-19*
