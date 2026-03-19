---
status: complete
phase: 01-foundation
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md]
started: 2026-03-18T21:37:40.8183457+01:00
updated: 2026-03-19T00:00:00+01:00
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Stop any running app process. Start the app from scratch. The server should boot without startup errors and /health should respond.
result: passed

### 2. Google Login Redirect
expected: Visiting /auth/login redirects to Google consent (or configured OAuth provider flow) without server error.
result: passed

### 3. OAuth Callback Creates/Logs In User
expected: After OAuth callback, user gets session cookie and is redirected to / with authenticated calendar page.
result: passed

### 4. Session Persistence
expected: Refreshing / after login keeps user authenticated (no forced logout).
result: passed

### 5. Invite Household Member
expected: Authenticated user can submit invite via /invite and receive a successful invitation message for a valid second email.
result: passed
note: Initial 500 → "Inviter has no calendar" fixed by provisioning missing calendar for existing OAuth users.
note: Follow-up 500 → "Inviter not found" reproduced for sessions where auth user id is external (non-local DB id). Fixed by resolving inviter by local id, external id (google_id), then email and creating/provisioning local inviter record when needed.
note: Regression tests added: test_invite_user_resolves_inviter_by_email_when_id_is_external and test_invite_user_resolves_inviter_by_external_id.
note: Latest 500 traced to Supabase RLS (`42501`) on `calendars` insert under anon/backend write path. Fixed by adding authenticated RLS policies (users/calendars/calendar_invitations) via Supabase migration and forwarding Supabase session token for invite write operations.
note: Latest 500 traced to Supabase RLS (`42501`) on `users` insert during inviter bootstrap. Fixed by including `google_id` on bootstrap user insert, passing external auth id from route/dependency, using auth-token-aware reads in `get_current_user`, and relaxing users select/update RLS to permit self-linking by JWT email.
note: Latest 500 traced to Supabase RLS (`42501`) on `calendars` insert for existing inviter rows without `google_id`. Fixed by broadening calendars/invitations authenticated policies to allow ownership checks via either `google_id` or JWT email, backfilling `google_id` before calendar create, and refreshing access token from `supabase_refresh` cookie in invite route when session cookie is legacy/stale.
note: Latest 500 traced to stale/non-Supabase bearer token being forwarded to PostgREST. Fixed by validating invite `db_auth_token` with `fetch_supabase_user`; if invalid, route refreshes from `supabase_refresh` before write operations.
note: Latest 500 traced to PostgREST `return=representation` behavior: calendar INSERT succeeded policy-wise, but SELECT on the newly inserted row was denied because select policy required `users.calendar_id = calendars.id` before user row was updated. Fixed by widening calendars SELECT policy to also allow owner (`users.id = calendars.owner_user_id`) for authenticated identity.
note: User re-verified manually on 2026-03-19: POST /api/users/invite returns 200 OK and invitation is sent.

### 6. Household Linking Visibility
expected: Household endpoint and calendar view reflect shared membership and common calendar visibility for linked users.
result: passed
note: User confirmed completion on 2026-03-19.

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

### GAP-1: Existing OAuth users missing calendar_id can't invite
- **Symptom:** POST /api/users/invite → 500 "Inviter has no calendar" for any re-authenticating user without a calendar row.
- **Root cause:** `_upsert_local_user_from_profile` (auth/routes.py) only created a calendar for brand-new users; returning users in the `else` branch had no calendar provisioned.
- **Fix applied:** Added calendar creation + `calendar_id` update in the `else` branch when `user.calendar_id` is None.
- **Verified:** `pytest tests/test_auth.py tests/test_users.py` → 7 passed.

### GAP-2: Invite endpoint used non-local auth user id
- **Symptom:** POST /api/users/invite → 500 "Inviter not found" after the first fix.
- **Root cause:** `invite_user` relied only on `inviter_id`; in some Supabase-authenticated sessions this id is external and not present in local `users` table.
- **Fix applied:** `UserService.invite_user` now resolves inviter by local id, external auth id (`google_id`), or fallback email, provisions local user/calendar if needed, and stores invitation with local inviter id.
- **Verified:** Added regression tests and reran `pytest tests/test_users.py tests/test_auth.py` → 8 passed.

### GAP-3: RLS blocked backend inserts for invite bootstrap
- **Symptom:** POST /api/users/invite failed with `RuntimeError: Supabase insert failed: 401 {"code":"42501", ... "new row violates row-level security policy for table \"calendars\""}`.
- **Root cause:** Public tables only had `service_role` RLS policies while app writes were executed with publishable/anon context for invite bootstrap operations.
- **Fix applied:** Added authenticated RLS policies for `users`, `calendars`, and `calendar_invitations` through Supabase migration `add_authenticated_rls_for_household_invites`; updated invite write path to pass caller Supabase access token to PostgREST and avoid sending legacy app JWT as DB auth token.
- **Verified:** Supabase policy query confirms authenticated policies exist; local tests remain green (`pytest tests/test_users.py tests/test_auth.py` → 8 passed).

### GAP-4: Users bootstrap insert violated users RLS
- **Symptom:** POST /api/users/invite failed with `RuntimeError: Supabase insert failed: 403 {"code":"42501", ... "new row violates row-level security policy for table \"users\""}`.
- **Root cause:** Invite bootstrap path created local user without `google_id`, violating users `INSERT` RLS (`google_id = auth.uid()`), and auth dependency could return fallback identity due tokenless lookups/side-effect errors.
- **Fix applied:**
  - Added `google_id` population in bootstrap `create_user` (`inviter_external_id or inviter_id`).
  - Passed external auth id from route (`user.google_id` or `user.id`) into service.
  - Updated `get_current_user` to use auth-token-aware repository calls and made invitation auto-accept best-effort.
  - Applied Supabase migration `relax_users_rls_for_email_self_linking` to allow authenticated select/update by either `google_id = auth.uid()` or JWT email match.
- **Verified:** `pytest tests/test_users.py tests/test_auth.py` → 8 passed.

### GAP-5: Calendars insert still blocked for partially linked inviter rows
- **Symptom:** POST /api/users/invite failed with `RuntimeError: Supabase insert failed: 403 {"code":"42501", ... "new row violates row-level security policy for table \"calendars\""}`.
- **Root cause:** Some existing inviter rows could be resolved by email but still had null/legacy `google_id`; calendars `INSERT` policy originally required strict `google_id = auth.uid()` ownership only.
- **Fix applied:**
  - Supabase migration `relax_calendar_and_invitation_rls_with_email_fallback` adds authenticated ownership checks by either `google_id` or JWT email for calendars/invitations select/insert/update.
  - Service now backfills inviter `google_id` before calendar bootstrap when external id is available.
  - Invite route now refreshes token from `supabase_refresh` if session cookie is legacy/stale and returns 401 guidance instead of 500 when no Supabase token is available.
- **Verified:** `pytest tests/test_users.py tests/test_auth.py` → 8 passed.

### GAP-6: Invite route forwarded invalid bearer token to PostgREST
- **Symptom:** Persistent 403 RLS failures on invite despite policy fixes.
- **Root cause:** Invite route could pass a stale/non-Supabase token from `session` cookie; PostgREST then evaluated request outside expected authenticated identity.
- **Fix applied:** Invite route now validates token with `fetch_supabase_user`; invalid token is discarded and replaced via refresh-token flow before DB writes.
- **Verified:** `pytest tests/test_users.py tests/test_auth.py` → 8 passed.

### GAP-7: Calendar INSERT return path blocked by SELECT policy
- **Symptom:** `Supabase insert failed ... table=calendars ... code=42501` persisted even with permissive INSERT check.
- **Root cause:** PostgREST `INSERT` with `Prefer: return=representation` performs a read of the inserted row; `calendars_authenticated_select` only allowed rows where `users.calendar_id = calendars.id`. During bootstrap, user `calendar_id` is still null at insert time, so SELECT was denied.
- **Fix applied:** Supabase migration `fix_calendars_select_for_insert_returning` changed calendars SELECT policy to allow authenticated identity when either `users.calendar_id = calendars.id` OR `users.id = calendars.owner_user_id`.
- **Expected outcome:** calendar insert-return succeeds, then user update sets `calendar_id`, and invite flow can continue.
