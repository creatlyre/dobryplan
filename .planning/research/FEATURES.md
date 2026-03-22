# Feature Research

**Domain:** Household calendar + budget app — v3.0 features
**Researched:** 2026-03-22
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|-------------|------------|-------|
| **Dashboard home page** — today's events, 7-day preview, budget snapshot | Every multi-feature app needs a landing page that surfaces what matters now. Users shouldn't navigate to 3 different pages to see their day. | **Low** | Aggregate view over existing APIs. No new data models. Render server-side from existing event repo + budget service. |
| **Event categories with colors** — preset + custom, color-coded grid cells | Google Calendar, Apple Calendar, Outlook all have color-coded categories. Users expect visual grouping of event types. Without it, a dense calendar is a wall of identical indigo blocks. | **Medium** | New `event_categories` table + `category_id` FK on events. Need 6-8 preset hex colors. Color shows as left-border or dot on month grid cells. |
| **Expense categories** — tag, filter, group expenses | Every budget tracker (YNAB, Mint, Goodbudget) groups expenses. Without categories, the expense list is flat and unanalyzable. | **Medium** | New `expense_categories` table + `category_id` FK on expenses. Category selector on expense forms. Filter/group on expense list page. |
| **Expense category charts** — pie chart for category breakdown | Visual breakdown is expected in any budget dashboard. Already have bar charts in stats page — adding pie/donut for categories is the natural next step. | **Low** | Pure frontend: aggregate expenses by category, render with CSS-only donut or lightweight JS. No new backend model beyond expense categories. |
| **Shared shopping list** — add/delete items, shared between both users | Core differentiator for *household* apps (Cozi, OurHome, FamilyWall all have it). If two people share a calendar and budget, they expect a shared list. | **Low-Medium** | New `shopping_items` table (id, calendar_id, text, checked, added_by, created_at). Simple CRUD. HTMX real-time checkbox toggling. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **In-app notification feed** — partner activity log | Most household apps show "Partner added X" as a feed. Keeps both users aware without constant verbal coordination. Unique in a self-hosted calendar context. | **Medium** | New `notifications` table (id, calendar_id, user_id, type, payload JSON, read boolean, created_at). Insert on event/expense CRUD. Render as dropdown or sidebar feed. Bell icon with unread count badge. |
| **Email notifications** — optional alerts for partner changes | Useful when one partner isn't actively checking the app. Opt-in only. Most household apps offer this (Cozi, FamilyWall). | **Medium-High** | Requires email sending infrastructure (SMTP or transactional service). User preference toggle (on/off, frequency: instant/daily digest). Must not spam. Consider daily digest as simpler v1. |
| **Per-category budget limits with alerts** — spending caps per category | YNAB's core feature. Transforms the budget from tracking to *planning*. Users set "max 500 PLN/month on groceries" and see a progress bar + warning when 80%+ used. | **Medium** | `budget_limit` field on expense_categories. Comparison logic in overview service. Visual progress bar on dashboard/overview. Alert threshold at 80% and 100%. |
| **Shopping list string parsing** — "milk, bread, eggs" → 3 items | Quality-of-life: paste or type a comma-separated string and get individual items. Matches the NLP quick-entry pattern already in the app. | **Low** | Frontend split on commas/newlines before POST. Or backend parse with simple string.split(). Trivial but feels polished. |
| **Dashboard quick-add** — create event or expense from home page | Reduces friction. User lands on dashboard, sees "add event" and "add expense" in one place. Re-use existing modals. | **Low** | Re-use `event_entry_modal.html` and existing expense form. Include via HTMX partial load on dashboard. No new logic. |
| **Custom event categories** — user-defined beyond presets | Let users add "Date Night", "Vet", "Kids" beyond the 5 presets. Household needs are idiosyncratic. | **Low** | Already building category CRUD — just add a "create custom" form. Same table, `is_preset=false`. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Real-time push notifications (WebSocket/SSE)** | "I want instant updates" | Adds WebSocket infrastructure, connection management, and complexity to a server-rendered HTMX app. Two-user model means the benefit is marginal. | Polling on dashboard (30s interval via HTMX `hx-trigger="every 30s"`). Notification badge updates on page load. |
| **Expense auto-categorization (ML/AI)** | "Categorize my expenses automatically" | Requires training data, ML pipeline, or LLM API calls. Over-engineered for a two-user household app with ~20-50 expenses/month. | Suggest last-used category for same expense name (simple string match). "Rent" → auto-fill "Housing". |
| **Shopping list with quantities, units, prices** | "Make it a full grocery manager" | Scope creep into a separate product (e.g., AnyList, OurGroceries). Adds complexity to what should be a simple checkbox list. | Keep it text-only with checked/unchecked. Users can write "Milk 2L" as free text. |
| **Notification preferences granularity** — per-event-type toggles | "Let me choose which notifications I get" | Complex preference UI, many toggle combinations, confusing. Two-user app doesn't need Gmail-level notification settings. | Single on/off toggle for in-app + single on/off for email. Maybe add "mute for today" later. |
| **Category color picker** — full hex/HSL picker | "Let me pick any color" | Custom color pickers are complex UI. Users pick ugly colors or colors with poor contrast on dark backgrounds. | Offer 10-12 curated palette colors that work on the dark glass UI. Dropdown grid, not a picker. |
| **Shared shopping list with multiple lists** | "We need separate lists for different stores" | Multi-list management adds navigation, naming, archiving complexity. | One shared list. Items can include store name as free text if needed (e.g., "Biedronka: mleko"). |
| **Dashboard widgets / customizable layout** | "Let me choose what shows on my dashboard" | Drag-and-drop widget systems are a significant frontend project. Two users with the same data need the same view. | Fixed, well-designed layout. Same for both users. Opinionated > configurable for a 2-person app. |

## Feature Dependencies

```
                    ┌──────────────────┐
                    │  Event Categories │
                    │  (new table + FK) │
                    └───────┬──────────┘
                            │ colors on grid
                            ▼
                    ┌──────────────────┐
                    │   Calendar Grid   │ (existing, needs color integration)
                    │   Month Grid      │
                    └──────────────────┘

                    ┌──────────────────┐
                    │ Expense Categories│
                    │ (new table + FK)  │
                    └───┬──────────┬───┘
                        │          │
              filter/group     category limits
                        │          │
                        ▼          ▼
              ┌─────────────┐  ┌──────────────┐
              │ Category     │  │ Budget Limit  │
              │ Charts       │  │ Alerts        │
              └─────────────┘  └──────────────┘

Event Categories ──┐
Expense Categories ─┤
Budget Service ─────┤──▶  ┌──────────────────┐
Event Repository ───┤     │    DASHBOARD      │ (aggregate view)
Shopping List ──────┘     │  (home page)      │
                          └──────────────────┘

Event CRUD hooks ──────▶  ┌──────────────────┐
Expense CRUD hooks ────▶  │  NOTIFICATIONS   │
Shopping list hooks ───▶  │  (in-app feed)   │
                          └───────┬──────────┘
                                  │ optional
                                  ▼
                          ┌──────────────────┐
                          │  Email Alerts    │
                          │  (SMTP/service)  │
                          └──────────────────┘

Shopping List ── independent, no dependencies on other new features
```

### Dependency Notes

1. **Event categories BEFORE dashboard** — dashboard should show color-coded events from day one. Building dashboard first then retrofitting colors is rework.
2. **Expense categories BEFORE dashboard** — dashboard budget snapshot should show top spending categories. Same reasoning.
3. **Notifications AFTER CRUD hooks** — notifications insert on create/update/delete of events/expenses. The CRUD endpoints must emit notification events, so categories + core CRUD changes come first.
4. **Email notifications AFTER in-app** — email is an extension of in-app notifications. Build the notification model and insertion logic first, add email delivery as a follow-on.
5. **Shopping list is independent** — no dependencies on categories, notifications, or dashboard. Can be built in parallel with anything.
6. **Dashboard is the LAST feature** — it aggregates everything else. Build the parts first, then the aggregate view.
7. **Charts depend on expense categories** — can't show category breakdown without categories. Build category model → tag existing expenses → render charts.

### Build Order Recommendation

```
Phase 1: Event Categories & Colors (model + calendar grid integration)
Phase 2: Expense Categories + Charts (model + expense page integration + pie chart)
Phase 3: Per-Category Budget Limits & Alerts
Phase 4: Shared Shopping List (independent, parallelizable)
Phase 5: Notification System (in-app feed, CRUD hooks)
Phase 6: Email Notifications (SMTP, user preferences)
Phase 7: Dashboard Home Page (aggregate view, last)
```

## Recommended v3.0 Scope

### Include Now (v3.0)

| Feature | Rationale |
|---------|-----------|
| Dashboard home page | Unifies the app experience. Without it, users land on a calendar they could get from Google. |
| Event categories with colors (5 presets + custom) | Visual identity for the calendar. Transforms usability. Low-medium effort. |
| Expense categories (presets + custom) | Enables meaningful budget analysis. Medium effort. |
| Expense category pie/bar charts | Natural extension of existing stats page. Low effort after categories exist. |
| Per-category budget limits with 80%/100% alerts | Transforms budget from tracking to planning. Medium effort but high value. |
| In-app notification feed | Essential for collaboration awareness. Medium effort. |
| Shared shopping list (simple text + checked/unchecked) | Households expect it. Low-medium effort. Independent buildable. |
| Shopping list string parsing | Low effort, polished feel. |
| Dashboard quick-add (reuse existing modals) | Low effort, high usability. |

### Defer to v3.1+

| Feature | Rationale |
|---------|-----------|
| Email notifications | Requires email infrastructure (SMTP config, templates, delivery). High complexity for a nice-to-have. Ship in-app first, validate demand. |
| Expense auto-categorization | Over-engineered. Simple "remember last category for same name" is sufficient. |
| Full color picker | Curated palette of 10-12 colors is better UX on dark theme. |
| Multiple shopping lists | One list is sufficient for a two-person household. Validate need first. |
| Dashboard customization | Fixed layout is appropriate for 2 users with identical data. |

### Complexity Budget

| Feature | Estimated Models | Estimated Routes | Estimated Templates | UI Impact |
|---------|-----------------|-----------------|---------------------|-----------|
| Event categories | 1 new table, 1 FK | 3-4 (CRUD) | event_form partial update, month_grid color | Month grid visual change |
| Expense categories | 1 new table, 1 FK | 3-4 (CRUD) | expense form update, new filter UI | Expense page update |
| Category charts | 0 | 1 (aggregation endpoint) | stats page addition or new section | Add to budget_stats.html |
| Budget limits | 1 field on category table | 1-2 (set/check limit) | progress bars on overview | Budget overview update |
| Shopping list | 1 new table | 4-5 (CRUD + parse) | 1 new template | New nav item, new page |
| Notifications (in-app) | 1 new table | 2-3 (list, mark-read) | Bell icon in nav, dropdown feed | base.html nav update |
| Dashboard | 0 new tables | 1-2 (aggregate) | 1 new template | New landing page, / route change |

**Total new Supabase tables: 4** (event_categories, expense_categories, shopping_items, notifications)
**Total new templates: 2-3** (dashboard.html, shopping_list.html, notification dropdown partial)
**Existing template modifications: 4-5** (month_grid, event_form, expense form, budget_stats, base.html nav)

## Sources

- Domain patterns from Google Calendar (color-coded events, category presets), YNAB (per-category budget limits, spending progress bars), Cozi Family Organizer (shared lists, activity feed), FamilyWall (notifications, household dashboard), Goodbudget (envelope-style category budgets, pie charts)
- Existing codebase analysis: models.py (no category fields), expense_schemas.py (no category), month_grid.html (single indigo color), budget_stats.html (bar chart pattern reusable)
- Confidence: HIGH — these are well-established patterns in household/family app domain with clear implementation paths in the existing FastAPI + HTMX + Supabase stack

