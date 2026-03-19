# Phase 4: Google Calendar Sync - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver Google Calendar sync for the shared household calendar: manual month export, automatic push on event create/update/delete, and token-safe operation for both household users. Scope is push/export behavior only (not full bidirectional conflict resolution).

</domain>

<decisions>
## Implementation Decisions

### Sync trigger model
- [auto] Keep push-only sync for v1: app -> Google Calendar.
- [auto] Manual export remains a dedicated action through sync API endpoint.
- [auto] Automatic sync runs after successful event create, update, and delete.
- [auto] Automatic sync is best-effort and must not block core event CRUD success.

### Household delivery behavior
- [auto] Sync fanout targets all users linked to the same household calendar.
- [auto] Each user gets a separate dedicated Google calendar for synced items.
- [auto] Event mapping uses app event id as stable private metadata for idempotent upsert/delete.
- [auto] Recurrence from app events is preserved in Google payload when RRULE exists.

### Error and reliability behavior
- [auto] Token refresh is attempted when access token is expired and refresh token exists.
- [auto] Refresh-token reuse is required (no forced rotation per sync action).
- [auto] `invalid_grant`/auth failures should degrade gracefully (skip affected user, continue others).
- [auto] Sync errors are surfaced in API responses where applicable (`errors` array) and do not crash unrelated workflows.

### API surface and UX contract
- [auto] Keep sync API endpoints lightweight and authenticated under `/api/sync`.
- [auto] `/api/sync/export-month` returns aggregated counts (`users_synced`, `events_synced`) plus `errors`.
- [auto] `/api/sync/status` returns readiness metadata for current household context.
- [auto] Preserve server-rendered architecture; no SPA-specific sync orchestration added in this phase.

### Claude's Discretion
- Internal retry/backoff tuning for Google API transient failures.
- Exact logging verbosity and message wording.
- Minor response shape enrichments that stay backward compatible with existing tests.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and acceptance
- `.planning/ROADMAP.md` - Phase 4 goal, requirements coverage (SYNC-01..SYNC-04), and pitfalls.
- `.planning/REQUIREMENTS.md` - Explicit SYNC requirement contracts.
- `.planning/PROJECT.md` - Product constraints: two-user household, push-first sync direction.

### Existing sync implementation anchors
- `app/sync/service.py` - Core Google sync fanout, token refresh handling, payload mapping, month export.
- `app/sync/routes.py` - Sync API contract (`/export-month`, `/status`).
- `app/events/routes.py` - Automatic sync hooks on create/update/delete.
- `main.py` - Router registration and app wiring.

### Verification and behavior coverage
- `tests/test_sync_api.py` - API-level assertions for export and status endpoints.
- `tests/test_sync_integration.py` - Event CRUD trigger behavior for sync push/delete.
- `.planning/phases/04-google-calendar-sync/04-01-SUMMARY.md` - Foundation decisions already executed.
- `.planning/phases/04-google-calendar-sync/04-02-SUMMARY.md` - API contract delivery summary.
- `.planning/phases/04-google-calendar-sync/04-03-SUMMARY.md` - CRUD auto-sync strategy summary.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/sync/service.py`: already encapsulates household fanout, token refresh path, and Google event upsert/delete logic.
- `app/sync/routes.py`: stable authenticated sync endpoints suitable for UI or job invocations.
- `app/events/routes.py`: proven hook points for automatic sync after core CRUD operations.

### Established Patterns
- API routes return concise JSON payloads with counts + errors instead of hard failures for partial sync issues.
- Event CRUD remains primary source of truth; sync side effects are intentionally non-blocking.
- OAuth token material is encrypted/decrypted through auth utilities before Google API usage.

### Integration Points
- Manual month export enters through `/api/sync/export-month` and delegates to `GoogleSyncService.export_month`.
- Automatic push enters through event route handlers and delegates to `GoogleSyncService.sync_event_for_household`.
- Sync status for household readiness enters through `/api/sync/status`.

</code_context>

<specifics>
## Specific Ideas

- Keep sync calendars user-distinct and human-readable (`CalendarPlanner Sync (<email-prefix>)`).
- Keep Google payload mapping deterministic (`cp_event_id` private extended property).
- Preserve recurrence fidelity by forwarding RRULE in Google event body when available.

</specifics>

<deferred>
## Deferred Ideas

- Full bidirectional Google -> app sync with conflict resolution.
- Calendar selection UI per user (choose existing Google calendar vs dedicated sync calendar).
- Retry queues/background workers for eventual consistency beyond request lifecycle.

</deferred>

---

*Phase: 04-google-calendar-sync*
*Context gathered: 2026-03-19*
