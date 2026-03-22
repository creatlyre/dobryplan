# Requirements: CalendarPlanner

**Defined:** 2026-03-22
**Core Value:** A shared calendar both partners can edit that stays in sync with Google Calendar, so the family schedule is always current everywhere.

## v3.0 Requirements

Requirements for milestone v3.0 — Dashboard, Notifications & Categories.

### Event Categories

- [ ] **ECAT-01**: User can assign an event to a category from preset list (Work, Personal, Health, Errands, Social)
- [ ] **ECAT-02**: User can create custom event categories with a name and curated palette color
- [ ] **ECAT-03**: Calendar month grid shows color-coded indicators (dot or border) per event category
- [ ] **ECAT-04**: User can filter calendar views by one or more categories
- [ ] **ECAT-05**: Category selector appears in event create and edit forms

### Expense Categories

- [ ] **XCAT-01**: User can assign an expense to a category from preset list (Groceries, Rent, Utilities, Transport, Entertainment, Health, Education, Other)
- [ ] **XCAT-02**: User can create custom expense categories
- [ ] **XCAT-03**: Monthly pie/bar chart shows spending breakdown per category on budget stats page
- [ ] **XCAT-04**: User can filter/group expense list by category
- [ ] **XCAT-05**: Category selector appears in expense create and edit forms (recurring + one-time)

### Notifications

- [ ] **NOTIF-01**: Bell icon in navigation shows unread notification count badge
- [ ] **NOTIF-02**: Dropdown/page shows notification feed of partner's event and budget changes
- [ ] **NOTIF-03**: User can mark individual notifications as read or dismiss them
- [ ] **NOTIF-04**: User can mark all notifications as read
- [ ] **NOTIF-05**: Notification is created when partner creates, edits, or deletes an event
- [ ] **NOTIF-06**: Notification is created when partner adds, edits, or deletes an expense/income entry
- [ ] **NOTIF-07**: Optional email notification sent for partner's event changes (user preference toggle)
- [ ] **NOTIF-08**: Event reminder notifications sent at configured reminder times before event start

### Shopping List

- [ ] **SHOP-01**: User can add items to a shared shopping list
- [ ] **SHOP-02**: User can delete items from the shopping list
- [ ] **SHOP-03**: User can check off / uncheck items on the shopping list
- [ ] **SHOP-04**: Both household users see and share the same shopping list
- [ ] **SHOP-05**: User can paste/type a comma-separated string to add multiple items at once

### Dashboard

- [ ] **DASH-01**: Home page shows today's events color-coded by category
- [ ] **DASH-02**: Home page shows compact 7-day upcoming events preview
- [ ] **DASH-03**: Home page shows budget snapshot (current month balance, top spending categories, income vs expenses)
- [ ] **DASH-04**: Home page provides quick-add buttons for creating events and expenses

## Future Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### Budget Enhancements

- **BLIM-01**: Per-category budget limits with 80%/100% spending alerts
- **BLIM-02**: Progress bar visualization for category spending vs limit

### Notification Enhancements

- **NOTIF-09**: Shopping list change notifications
- **NOTIF-10**: Daily digest email summarizing all partner changes
- **NOTIF-11**: Notification preference granularity (per event type toggles)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| WebSocket/SSE real-time push | Over-engineered for 2-user app; HTMX polling sufficient |
| ML/AI expense auto-categorization | Over-engineered; suggest-last-used pattern is simpler |
| Shopping list with quantities/units/prices | Scope creep into separate product; free-text is sufficient |
| Full color picker for categories | Complex UI; curated palette colors work better |
| Multiple shopping lists | One shared list is sufficient; store name in item text |
| Customizable dashboard layout | Fixed layout is correct for 2-user household app |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ECAT-01 | - | Pending |
| ECAT-02 | - | Pending |
| ECAT-03 | - | Pending |
| ECAT-04 | - | Pending |
| ECAT-05 | - | Pending |
| XCAT-01 | - | Pending |
| XCAT-02 | - | Pending |
| XCAT-03 | - | Pending |
| XCAT-04 | - | Pending |
| XCAT-05 | - | Pending |
| NOTIF-01 | - | Pending |
| NOTIF-02 | - | Pending |
| NOTIF-03 | - | Pending |
| NOTIF-04 | - | Pending |
| NOTIF-05 | - | Pending |
| NOTIF-06 | - | Pending |
| NOTIF-07 | - | Pending |
| NOTIF-08 | - | Pending |
| SHOP-01 | - | Pending |
| SHOP-02 | - | Pending |
| SHOP-03 | - | Pending |
| SHOP-04 | - | Pending |
| SHOP-05 | - | Pending |
| DASH-01 | - | Pending |
| DASH-02 | - | Pending |
| DASH-03 | - | Pending |
| DASH-04 | - | Pending |

**Coverage:**
- v3.0 requirements: 27 total
- Mapped to phases: 0
- Unmapped: 27

---
*Requirements defined: 2026-03-22*
*Last updated: 2026-03-22 after milestone v3.0 scoping*
