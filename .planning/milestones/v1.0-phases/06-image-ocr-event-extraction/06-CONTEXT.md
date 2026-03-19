# Phase 6: Image / OCR Event Extraction - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Add image-based event extraction to Quick Add so users can upload a flyer/screenshot, review extracted fields with confidence cues, edit everything before save, and fall back to manual entry when OCR cannot parse safely.

Scope for this phase is OCR upload -> extraction -> review/fallback in existing modal flow. It does not introduce background workers, queues, or external storage.

</domain>

<decisions>
## Implementation Decisions

- OCR entry is a new Scan Image action inside the existing Quick Add modal.
- OCR extraction endpoint lives under existing events API (`/api/events/ocr-parse`) and returns structured data plus raw text.
- EasyOCR integration is optional-at-runtime; if unavailable, endpoint returns actionable OCR-unavailable error instead of crashing.
- OCR extraction is always user-reviewed before save; no auto-save behavior.
- Review fields reuse existing quick-add review editor and remain fully editable.
- Low-confidence extraction is surfaced with confidence note in review and yellow field highlighting already used by quick-add.
- OCR failures route to fallback form with raw extracted text visible.

### Claude's Discretion

- Exact phrasing of confidence notes and OCR error messages.
- Internal confidence thresholds and aggregation strategy.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/ROADMAP.md` - phase boundary, goals, and OCR success criteria.
- `.planning/REQUIREMENTS.md` - OCR-01, OCR-02, OCR-03 contracts.
- `app/templates/calendar.html` - existing quick-add state machine.
- `app/templates/partials/quick_add_modal.html` - quick-add markup extension point.
- `app/events/routes.py` - parse endpoint patterns and auth/timezone behavior.
- `app/events/nlp.py` - reuse parser for OCR text extraction post-processing.

</canonical_refs>

<code_context>
## Existing Code Insights

- Quick Add already supports parse -> review -> save and fallback flows.
- Existing review UI already supports confidence-based field highlighting.
- Event save contract is stable and should be reused by OCR path.

</code_context>

<specifics>
## Specific Ideas

- Keep OCR path in the same modal to avoid context switching.
- Preserve accessibility live-region announcements for OCR transitions.
- Ensure API tests do not depend on local EasyOCR install by monkeypatching OCR service.

</specifics>

<deferred>
## Deferred Ideas

- Asynchronous OCR job queue and progress notifications.
- Persisting uploaded source images for audit/history.
- Multi-language OCR models.

</deferred>

---

*Phase: 06-image-ocr-event-extraction*
*Context gathered: 2026-03-19*