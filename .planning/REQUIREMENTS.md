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

- [x] **I18N-01**: First-time and signed-in users see Polish UI copy by default across the application
- [x] **I18N-02**: User can switch application language between Polish and English from core navigation
- [x] **I18N-03**: Selected language persists across page refresh and subsequent sessions for the same user
- [x] **I18N-04**: Calendar, auth, events, sync, NLP, and OCR user-facing labels/messages are available in both Polish and English
- [x] **I18N-05**: Date and time presentation follows selected locale conventions (Polish vs English)
- [x] **I18N-06**: Automated test coverage verifies Polish default and English switching behavior on key user flows
- [x] **I18N-07**: NLP and OCR parsing accept Polish phrases and diacritics with behavior parity to English parsing flows

## v2.0 Requirements

### Budget Settings (BSET)

- [ ] **BSET-01**: User can configure 3 hourly rates (Rate 1, Rate 2, Rate 3) in PLN from a settings UI
- [ ] **BSET-02**: User can configure flat monthly costs (ZUS + accounting) that apply to every month
- [ ] **BSET-03**: User can set an initial bank account balance in settings
- [ ] **BSET-04**: User can access budget settings from the main app navigation
- [ ] **BSET-05**: User can adjust initial balance and rates at any time from settings

### Income Calculation (INC)

- [ ] **INC-01**: User can enter hours worked per rate (Time 1, Time 2, Time 3) for each month of the year
- [ ] **INC-02**: Hours default to 160 when left blank
- [ ] **INC-03**: System calculates gross earnings per month: Rate1*Time1 + Rate2*Time2 + Rate3*Time3
- [ ] **INC-04**: System calculates net pension per month: (Time1*Rate1)*0.88 + (Time2*Rate2)*0.88 + (Time3*Rate3)*0.88 - Costs
- [ ] **INC-05**: User can enter additional household earnings per month (partner salary, ZUS child bonuses - multiple entries allowed)

### Expenses (EXP)

- [ ] **EXP-01**: User can add recurring monthly expenses with name and amount
- [ ] **EXP-02**: User can add one-time expenses with name, amount, and target month
- [ ] **EXP-03**: User can edit and delete both recurring and one-time expenses
- [ ] **EXP-04**: Recurring expenses sum is applied to every month automatically

### Year Overview (YOV)

- [ ] **YOV-01**: User sees a 12-month table showing: Month | Monthly Expenses | Additional Expenses | +/- on Month | Account End of Month
- [ ] **YOV-02**: +/- on Month is calculated as: Net Pension + Additional Earnings - Recurring Expenses - One-Time Expenses
- [ ] **YOV-03**: Account End of Month is: Previous month account balance + current month +/-
- [ ] **YOV-04**: January Account End of Month starts from the initial bank balance setting
- [ ] **YOV-05**: Year overview recalculates automatically when any input changes

### Budget Localization (BL)

- [ ] **BL-01**: Budget Tracker UI is available in Polish (required) and English (optional, via existing i18n system if low effort)

## Future Requirements

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

- **CEXP-01**: User can export calendar to .ics file for import into any calendar app

### Event Visibility Controls

- **PRIV-01**: User can choose visibility per event (shared or private) when creating or editing events
- **PRIV-02**: Private events are visible only to the event owner in household month/day views and APIs
- **PRIV-03**: Shared events sync to both linked Google calendars; private events sync only to owner's Google calendar
- **PRIV-04**: Quick Add and manual modal both expose visibility selection and preserve it through parse/review/save flows

### Multi-Year Budget

- **MYBUDGET-01**: User can select and switch between budget years (e.g., 2026, 2027)
- **MYBUDGET-02**: User can import past budget data from Excel

## Out of Scope

| Feature | Reason |
|---------|--------|
| More than two users / family group calendars | Household pair is the scoped use case; multi-user adds significant ACL complexity |
| Native mobile app | Google Calendar on phone handles mobile via sync |
| Full two-way Google Calendar sync | Two-way sync requires conflict resolution strategy; push-only covers the core need |
| Outlook / Apple Calendar integration | Google Calendar is the stated requirement |
| Multi-year budget tracking | Current year only for v2.0; future years deferred |
| Excel import for past budget data | Optional convenience; not required for v2.0 |
| Budget-to-calendar event integration | Budget and calendar are independent features |

## Traceability

| Requirement | Phase | Goal | Status |
|-------------|-------|------|--------|
| I18N-01 | Phase 8 | Localization foundation and Polish default | Shipped v1.1 |
| I18N-04 | Phase 8 | Localization foundation and Polish default | Shipped v1.1 |
| I18N-05 | Phase 8 | Localization foundation and Polish default | Shipped v1.1 |
| I18N-02 | Phase 9 | Language switcher, persistence, and translation coverage | Shipped v1.1 |
| I18N-03 | Phase 9 | Language switcher, persistence, and translation coverage | Shipped v1.1 |
| I18N-06 | Phase 9 | Language switcher, persistence, and translation coverage | Shipped v1.1 |
| I18N-07 | Phase 10 | Verify parser works with Polish language after localization | Shipped v1.1 |
| BSET-01 | Phase 12 | Budget Data Foundation & Settings UI | Pending |
| BSET-02 | Phase 12 | Budget Data Foundation & Settings UI | Pending |
| BSET-03 | Phase 12 | Budget Data Foundation & Settings UI | Pending |
| BSET-04 | Phase 12 | Budget Data Foundation & Settings UI | Pending |
| BSET-05 | Phase 12 | Budget Data Foundation & Settings UI | Pending |
| BL-01 | Phase 12 | Budget Data Foundation & Settings UI | Pending |
| INC-01 | Phase 13 | Income Calculation Engine | Pending |
| INC-02 | Phase 13 | Income Calculation Engine | Pending |
| INC-03 | Phase 13 | Income Calculation Engine | Pending |
| INC-04 | Phase 13 | Income Calculation Engine | Pending |
| INC-05 | Phase 13 | Income Calculation Engine | Pending |
| EXP-01 | Phase 14 | Expense Management | Pending |
| EXP-02 | Phase 14 | Expense Management | Pending |
| EXP-03 | Phase 14 | Expense Management | Pending |
| EXP-04 | Phase 14 | Expense Management | Pending |
| YOV-01 | Phase 15 | Year Overview Dashboard | Pending |
| YOV-02 | Phase 15 | Year Overview Dashboard | Pending |
| YOV-03 | Phase 15 | Year Overview Dashboard | Pending |
| YOV-04 | Phase 15 | Year Overview Dashboard | Pending |
| YOV-05 | Phase 15 | Year Overview Dashboard | Pending |

**Coverage:**
- v2.0 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-03-18*
*Last updated: 2026-03-20 after creating v2.0 Budget Tracker roadmap*
