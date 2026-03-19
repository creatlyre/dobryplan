# Requirements: CalendarPlanner

**Defined:** 2026-03-18
**Core Value:** A shared calendar both partners can edit that stays in sync with Google Calendar, so the family schedule is always current everywhere - on the web and on their phones.

## v1 Requirements

### Authentication and Users

- [x] **AUTH-01**: User can sign in with their Google account via OAuth2
- [x] **AUTH-02**: Two users can be linked to a single shared calendar household
- [x] **AUTH-03**: User session persists across browser refresh

### Event Management

- [x] **EVT-01**: User can create a one-time event with title, date, time, and optional description
- [x] **EVT-02**: User can create a recurring event (daily, weekly, monthly, yearly)
- [x] **EVT-03**: User can edit an event (title, date, time, description)
- [x] **EVT-04**: User can delete an event
- [x] **EVT-05**: User can view a list of upcoming events for the current day
- [x] **EVT-06**: User can view a list of upcoming events for the current month
- [x] **EVT-07**: Both users see events created by either user in the shared calendar

### Calendar Views

- [x] **VIEW-01**: User can view events in a monthly calendar grid
- [x] **VIEW-02**: User can navigate between months
- [x] **VIEW-03**: Events show basic info (title, time) in the calendar grid

### Google Calendar Sync

- [x] **SYNC-01**: User can export all events for a given month to their Google Calendar
- [x] **SYNC-02**: Newly created events are automatically pushed to the linked Google Calendar
- [x] **SYNC-03**: Event deletions are reflected in Google Calendar
- [x] **SYNC-04**: Both users' Google Calendars receive synced events

### Natural Language Input

- [x] **NLP-01**: User can type a natural language event description and the app parses it into a structured event for review
- [x] **NLP-02**: Parsed event is shown for confirmation before saving
- [x] **NLP-03**: User can correct any parsed fields before saving

### Image / OCR Event Extraction

- [x] **OCR-01**: User can upload an image and the app extracts date, time, and event name
- [x] **OCR-02**: Extracted event data is shown for review with a confidence indicator before saving
- [x] **OCR-03**: User can edit extracted fields before saving to calendar

## v1.1 Requirements

### Localization and Language Switching

- [ ] **I18N-01**: First-time and signed-in users see Polish UI copy by default across the application
- [ ] **I18N-02**: User can switch application language between Polish and English from core navigation
- [ ] **I18N-03**: Selected language persists across page refresh and subsequent sessions for the same user
- [ ] **I18N-04**: Calendar, auth, events, sync, NLP, and OCR user-facing labels/messages are available in both Polish and English
- [ ] **I18N-05**: Date and time presentation follows selected locale conventions (Polish vs English)
- [ ] **I18N-06**: Automated test coverage verifies Polish default and English switching behavior on key user flows
- [x] **I18N-07**: NLP and OCR parsing accept Polish phrases and diacritics (ą, ć, ę, ł, ń, ó, ś, ź, ż) with behavior parity to English parsing flows

## v2 Requirements

### Real-Time Collaboration

- **RT-01**: Changes made by one user appear in the other user's view within seconds (SSE or WebSocket push)
- **RT-02**: Conflict detection when both users edit the same event simultaneously

### Scheduling and Reminders

- **REM-01**: User receives browser notifications for upcoming events
- **REM-02**: User can set a custom reminder time per event

### Calendar Views (Extended)

- **VIEW-04**: Weekly view
- **VIEW-05**: Agenda / list view spanning multiple weeks

### Advanced Recurrence

- **RRULE-01**: User can edit a single occurrence of a recurring event without affecting others
- **RRULE-02**: User can end a recurring event series at a specific date

### Export

- **EXP-01**: User can export calendar to .ics file for import into any calendar app

### Event Visibility Controls

- **PRIV-01**: User can choose visibility per event (shared or private) when creating or editing events
- **PRIV-02**: Private events are visible only to the event owner in household month/day views and APIs
- **PRIV-03**: Shared events sync to both linked Google calendars; private events sync only to owner's Google calendar
- **PRIV-04**: Quick Add and manual modal both expose visibility selection and preserve it through parse/review/save flows

## Out of Scope

| Feature | Reason |
|---------|--------|
| More than two users / family group calendars | Household pair is the scoped use case for v1; multi-user adds significant ACL complexity |
| Native mobile app | Google Calendar on phone handles mobile via sync |
| Full two-way Google Calendar sync (v1) | Two-way sync requires conflict resolution strategy; push-only covers the core need and ships faster |
| Outlook / Apple Calendar integration | Out of scope v1; Google Calendar is the stated requirement |
| AI-generated event suggestions | Nice idea but not in stated requirements |
| Shopping lists, tasks, to-dos | Focus on events only; avoids feature bloat |
| Event visibility controls (PRIV-01..PRIV-04) in v1.1 | Deferred to next milestone to ship localization baseline first |

## Traceability

| Requirement | Phase | Goal | Status |
|-------------|-------|------|--------|
| I18N-01 | Phase 8 | Localization foundation and Polish default | Pending |
| I18N-04 | Phase 8 | Localization foundation and Polish default | Pending |
| I18N-05 | Phase 8 | Localization foundation and Polish default | Pending |
| I18N-02 | Phase 9 | Language switcher, persistence, and translation coverage | Pending |
| I18N-03 | Phase 9 | Language switcher, persistence, and translation coverage | Pending |
| I18N-06 | Phase 9 | Language switcher, persistence, and translation coverage | Pending |
| I18N-07 | Phase 10 | Verify parser works with Polish language after localization | Pending |

**Coverage:**
- v1.1 requirements: 7 total
- Mapped to phases: 7
- Unmapped: 0

---
*Requirements defined: 2026-03-18*
*Last updated: 2026-03-19 after starting v1.1 localization milestone*


