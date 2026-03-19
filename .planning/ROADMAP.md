# Roadmap: CalendarPlanner

**Milestone:** v1.0  
**Granularity:** Standard  
**Requirements Covered:** 23/23 v1 requirements  
**Last Updated:** 2026-03-18

---

## Phases

- [x] **Phase 1: Foundation** - Database, OAuth2 authentication, two-user authorization model
- [x] **Phase 2: Core Event Management** - Event CRUD operations and calendar grid/list views  
- [x] **Phase 3: Recurring Events** - RFC5545 RRULE support with timezone/DST handling
- [x] **Phase 4: Google Calendar Sync** - Push-based sync to Google Calendar with token management
- [x] **Phase 5: Natural Language Input** - dateparser-based event creation from text descriptions
- [x] **Phase 6: Image / OCR Event Extraction** - Image upload and date/time extraction with review

---
**Requirements Covered:** AUTH-01, AUTH-02, AUTH-03, EVT-07 (4 total)
- [ ] **Phase 7: UI/UX Improvements** - Navigation affordances, form validation feedback, modal-based event entry

- Project scaffolding complete (FastAPI, SQLAlchemy, Supabase PostgreSQL initialized)
- Google OAuth2 credentials created in Google Cloud Console

**Success Criteria:**
1. User can sign in with Google account via OAuth2 and land on authenticated calendar page
2. Two users can be invited/linked to a single shared calendar by email
3. Both users see the same calendar and events regardless of who created them  
4. User session persists across browser refresh and multiple tabs
5. Database schema supports events, users, recurring rules, and sync metadata

**Pitfalls Addressed:**
- OAuth2 refresh token exhaustion: store one token per user permanently; implement token reuse + error handling for `invalid_grant`

**Plans:** 3/3 complete

- [x] 01-01-PLAN.md - FastAPI scaffold + Supabase ORM models
- [x] 01-02-PLAN.md - OAuth2 login + JWT session middleware
- [x] 01-03-PLAN.md - Two-user invitations + shared household flow + tests

---

### Phase 2: Core Event Management
**Goal:** Users can create, edit, delete events and view them in calendar grid and upcoming lists.

**Requirements Covered:** EVT-01, EVT-03, EVT-04, EVT-05, EVT-06, VIEW-01, VIEW-02, VIEW-03 (8 total)

**Entry Conditions:**
- Phase 1 complete (auth, user model, database schema)
- EventService skeleton in place

**Success Criteria:**
1. User can create a one-time event with title, date, time, optional description from web form
2. User can edit any event (title, date, time, description) and see changes reflected immediately in UI
3. User can delete an event and it disappears from both users' views
4. User can view a list of upcoming events for the current day with times
5. User can view all events for the current month in a grid layout (month view)
6. User can navigate forward/backward between months in calendar view
7. Events display title and time in calendar grid cells
8. Calendar UI is responsive and works on mobile browser

**Pitfalls Addressed:**
- Concurrent edit conflicts: implement `last_edited_at` + `last_editor_id` fields for future conflict detection UI

**Plans:** 4/4 complete

- [x] 02-01-PLAN.md - Event domain contracts, repository, service
- [x] 02-02-PLAN.md - Authenticated event CRUD APIs + tests
- [x] 02-03-PLAN.md - Month/day calendar views + navigation
- [x] 02-04-PLAN.md - Interactive UI CRUD integration + integration tests

---

### Phase 3: Recurring Events
**Goal:** Support daily, weekly, monthly, yearly recurring events with proper RFC5545 RRULE and timezone/DST safety.

**Requirements Covered:** EVT-02 (1 total)

**Entry Conditions:**
- Phase 2 complete (event CRUD and views)
- RecurrenceService skeleton with `dateutil.rrule` integration

**Success Criteria:**
1. User can create a recurring event specifying frequency (daily, weekly, monthly, yearly)
2. User can set occurrence count or end date for recurring event series
3. All recurring event instances display correctly in calendar grid and list views
4. Recurring events handle DST boundaries correctly (Mar/Nov transitions)
5. All event times are stored internally in UTC and displayed in user's local timezone
6. Recurring event changes over time appear accurate when navigating between months

**Pitfalls Addressed:**
- Timezone/DST disasters: store all times in UTC; render to user's timezone only at UI; hard-test DST boundaries (Nov 5, Mar 9)
- In v1, disallow editing single recurrence instances; treat as separate events

**Plans:** 2/2 complete

- [x] 03-01-PLAN.md - recurrence engine + service integration
- [x] 03-02-PLAN.md - recurrence UI inputs + view expansion tests

---

### Phase 4: Google Calendar Sync
**Goal:** Automatically export and push household calendar events to both users' Google Calendars for phone reminders and mobile access.

**Requirements Covered:** SYNC-01, SYNC-02, SYNC-03, SYNC-04 (4 total)

**Entry Conditions:**
- Phase 1 complete (OAuth2 refresh token handling)
- Phases 2-3 complete (event CRUD, recurring events)
- GoogleSyncService skeleton with `google-api-python-client` integration

**Success Criteria:**
1. User can manually export all events for a given month to their Google Calendar with one click
2. Newly created events are automatically pushed to both users' Google Calendars within 5 seconds
3. Event deletions in shared calendar are reflected in both users' Google Calendars
4. Both users receive synced events in their own Google Calendar (user1-sync, user2-sync separate calendars)
5. Refresh token doesn't expire/exhaust between sync operations (tokens reused, not rotated on each call)
6. Sync failures are logged and user is notified if sync breaks; app remains functional

**Pitfalls Addressed:**
- Refresh token exhaustion: reuse single token per user; implement `invalid_grant` error recovery (flag user for re-auth)
- Google Calendar API quota batching: batch multiple event push operations per request

**Plans:** 3/3 complete

- [x] 04-01-PLAN.md - Google sync service foundation
- [x] 04-02-PLAN.md - month export + sync status APIs
- [x] 04-03-PLAN.md - automatic sync hooks on event CRUD

---

### Phase 5: Natural Language Input
**Goal:** Users can quickly add events by typing natural language descriptions (e.g., "dentist Thursday 2pm").

**Requirements Covered:** NLP-01, NLP-02, NLP-03 (3 total)

**Entry Conditions:**
- Phase 2 complete (event CRUD)
- Phase 3 complete (recurring event support)
- NLPService skeleton with `dateparser` integration

**Success Criteria:**
1. User can type "dentist Thursday 2pm" in a natural language input box and the app parses it into structured event (title, date, time)
2. Parsed event is displayed for user confirmation before saving (shows extracted title, date/time in calendar format)
3. User can correct any parsed fields (title, date, time) in the review form before committing to calendar
4. Parsing validates future dates; if ambiguous (e.g., "March 15" in December), app asks user "Did you mean 2026 or 2027?"
5. Parsing works with relative dates ("next Friday", "in 3 days", "tomorrow at 4pm")

**Pitfalls Addressed:**
- NLP date edge cases: validate against user's timezone + current date; limit initial implementation to explicit/relative formats; add user confirmation step

**Plans:** 5/5 complete

- [x] 05-01-PLAN.md - NLP parsing service + /api/events/parse endpoint
- [x] 05-02-PLAN.md - quick-add modal UI + parse/review/save orchestration  
- [x] 05-03-PLAN.md - error handling, confidence highlighting, fallback form, a11y
- [x] 05-04-PLAN.md - NLP parser gap fixes (weekday anchors, relative dates, timezone propagation)
- [x] 05-05-PLAN.md - ambiguity-year confirmation flow in quick-add UI + integration tests

---

### Phase 6: Image / OCR Event Extraction
**Goal:** Users can photograph event flyers/invitations and extract date/time/event name with human review before saving.

**Requirements Covered:** OCR-01, OCR-02, OCR-03 (3 total)

**Entry Conditions:**
- Phase 2 complete (event CRUD)
- Phase 5 complete (natural language parsing patterns established)
- OCRService skeleton with `EasyOCR` integration

**Success Criteria:**
1. User can upload an image (flyer, screenshot, invitation) and the app extracts date, time, and event name automatically
2. Extracted event data is shown in a review form with a confidence indicator per field (e.g., "Date: 87% confident")
3. Low-confidence fields (~<75%) are highlighted in yellow to alert user for manual review
4. User can edit extracted fields (title, date, time) before saving to calendar
5. If OCR fails entirely, app shows raw extracted text and a form fallback for manual entry
6. Image extraction happens asynchronously with user notification when complete

**Pitfalls Addressed:**
- OCR accuracy fallback: never auto-add results; always require human review; show raw image + extracted text
- Validate before sync: date in future, title not empty, location not garbage; highlight uncertain fields

**Plans:** 1/1 complete

- [x] 06-01-PLAN.md - OCR service + image parse endpoint + quick-add scan/review/fallback integration

---
## Progress
### Phase 7: UI/UX Improvements
**Goal:** Eliminate navigation friction and improve event entry workflow through targeted UX fixes: back navigation on invite page, modal-based event input, user-friendly date/time picker, and real-time form validation.

**Requirements Covered:** None (UX polish phase, all v1 functional requirements met)

**Entry Conditions:**
- Phase 5 complete (glassmorphism visual redesign + light/dark theme)
- Phase 6 complete (all functional requirements met)

**Success Criteria:**
1. Invite page displays back button that navigates to `/calendar`
2. Event entry modal opens/closes without errors and integrates with glassmorphism theme
3. Date and time inputs render as separate fields with user-friendly pickers
4. Form validation prevents invalid submissions and shows real-time error feedback
5. Submit button state correctly reflects validation result (enabled/disabled)
6. All modal and form styles match glassmorphism design system
7. All 52 existing tests pass (no regressions)
8. Keyboard navigation works: Tab cycles focus, Escape closes modal, E key opens modal
9. Mobile responsive: full-width modal, 44px+ touch targets, form flows naturally

**Pitfalls Addressed:**
- Navigation trap on invite page: add affordance (back button) to return to calendar
- Event entry friction: sidebar form cumbersome; move to floating modal for clarity
- Form validation: client-side instant feedback prevents invalid submissions
- Date/time UX: replace datetime-local with separate date + time inputs using native pickers

**Plans:** 4/4 planned (ready for execution)

- [ ] 07-01-PLAN.md - Back button + modal structure
- [ ] 07-02-PLAN.md - Date/time picker inputs + validation logic
- [ ] 07-03-PLAN.md - Keyboard shortcuts + accessibility audit
- [ ] 07-04-PLAN.md - Mobile responsive polish + test coverage

---

| Phase | Plans Complete | Status | Completed |
|-------|---|--------|-----------|
| 1. Foundation | 3/3 | Complete | 2026-03-18 |
| 2. Core Event Management | 4/4 | Complete | 2026-03-18 |
| 3. Recurring Events | 2/2 | Complete | 2026-03-18 |
| 4. Google Calendar Sync | 3/3 | Complete | 2026-03-18 |
| 5. Natural Language Input | 5/5 | Complete | 2026-03-19 |
| 6. Image / OCR | 1/1 | Complete | 2026-03-19 |
| **TOTAL** | **18/18** | **Complete** | 2026-03-19 |

| 7. UI/UX Improvements | 0/4 | Planned | 2026-03-19 |
| **TOTAL** | **18/22** | **In Progress** | 2026-03-19 |

## Coverage Validation

✅ **Complete coverage:** All 23 v1 requirements mapped to exactly one phase  
✅ **No orphans:** Every requirement appears in mapping  
✅ **No duplicates:** Each requirement assigned once

### Requirement Traceability

| Category | Requirement | Phase | Status |
|----------|-------------|-------|--------|
| **Auth** | AUTH-01: Sign in with Google OAuth2 | Phase 1 | Complete |
| | AUTH-02: Two users linked to shared calendar | Phase 1 | Complete |
| | AUTH-03: Session persists across refresh | Phase 1 | Complete |
| **Events** | EVT-01: Create one-time event | Phase 2 | Complete |
| | EVT-02: Create recurring event | Phase 3 | Complete |
| | EVT-03: Edit event | Phase 2 | Complete |
| | EVT-04: Delete event | Phase 2 | Complete |
| | EVT-05: View upcoming events (day) | Phase 2 | Complete |
| | EVT-06: View upcoming events (month) | Phase 2 | Complete |
| | EVT-07: Both users see shared events | Phase 1 | Complete |
| **Views** | VIEW-01: Month calendar grid | Phase 2 | Complete |
| | VIEW-02: Navigate months | Phase 2 | Complete |
| | VIEW-03: Events show title/time | Phase 2 | Complete |
| **Sync** | SYNC-01: Export month to Google Calendar | Phase 4 | Complete |
| | SYNC-02: Auto-push new events | Phase 4 | Complete |
| | SYNC-03: Reflected deletions | Phase 4 | Complete |
| | SYNC-04: Both users' calendars synced | Phase 4 | Complete |
| **NLP** | NLP-01: Parse natural language | Phase 5 | Complete |
| | NLP-02: Show parsed event for confirmation | Phase 5 | Complete |
| | NLP-03: Allow user to correct fields | Phase 5 | Complete |
| **OCR** | OCR-01: Upload image and extract | Phase 6 | Complete |
| | OCR-02: Show with confidence + review | Phase 6 | Complete |
| | OCR-03: Edit extracted fields | Phase 6 | Complete |

---

*Roadmap created: 2026-03-18 by roadmapper*  
*Next step: `/gsd-complete-milestone`*
