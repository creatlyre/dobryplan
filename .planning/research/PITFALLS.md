# Pitfalls Research

**Domain:** Household calendar + budget app — v3.0 additions (dashboard, notifications, event/expense categories, shopping list)
**Researched:** 2026-03-22
**Confidence:** HIGH (based on direct codebase analysis of existing architecture patterns)

---

## Critical Pitfalls

### Pitfall 1: Dashboard N+1 Query Explosion via Supabase REST

**What goes wrong:** The dashboard aggregates data from 4+ tables (events, expenses, income, shopping list). Each widget makes its own `SupabaseStore.select()` call over HTTP. With the existing pattern of one-REST-call-per-query, the dashboard page triggers 6-10 sequential HTTP round-trips to Supabase on every load — today's events, next 7 days, current month budget summary, recent notifications, shopping list count — causing 1-4 seconds of latency (200-400ms per call × 6-10 calls).

**Why it happens:** The existing repository pattern (`ExpenseRepository`, `EventRepository`, etc.) each make individual HTTP calls. A dashboard service that reuses these repositories will serialize all calls. Developers naturally reuse existing service methods rather than building purpose-built aggregation.

**How to avoid:**
- Use `concurrent.futures.ThreadPoolExecutor` to parallelize 4-5 independent Supabase REST calls within the dashboard endpoint. The app uses synchronous `httpx.Client` (singleton `_get_shared_client()`), so async requires a thread pool.
- Alternatively, create a Supabase RPC function that returns all dashboard data in one call.
- Cache dashboard data for 30-60 seconds in a simple dict with TTL — only 2 users, no Redis needed.
- Set a performance budget: dashboard must load in <500ms.

**Warning signs:** Dashboard page load >1 second; widgets appearing sequentially; timeout errors on slow connections.

**Phase to address:** Dashboard phase — design the aggregation approach before building widgets. Build dashboard LAST after all data sources exist.

---

### Pitfall 2: Adding `category_id` to Events/Expenses — Large Blast Radius

**What goes wrong:** Adding a `category_id` FK to the `events` and `expenses` tables requires handling ~all existing rows with NULL category. Every query, mapper function (`_to_event()`, `_to_expense()`), repository, service, route, and template that touches events/expenses needs updating simultaneously — 15+ files. With ~270 tests constructing `Event`/`Expense` objects, a schema change can break dozens of tests.

**Why it happens:** The dataclass models are tightly coupled to Supabase row shape via mapper functions. Adding a field means: model → mapper → repository → service → route → template — full stack change. Tests construct models directly with positional/keyword args.

**How to avoid:**
- Make `category_id` **nullable** with default `None`. Never require category on existing records.
- Add `category_id` and `category_name`/`category_color` as optional fields to `Event`/`Expense` dataclasses with defaults — keeps all existing test fixtures valid.
- Create categories tables first, then add nullable FK columns, then update mappers — in separate testable steps.
- Do NOT attempt retroactive bulk-assignment. Let users categorize going forward, or offer optional one-time "categorize past expenses" UI later.
- Single Supabase migration file: create categories table + add nullable FK.

**Warning signs:** Test suite starts failing after model changes; existing CRUD breaks; NULL category causes template rendering errors (`.category_name` on None).

**Phase to address:** Categories phase — migration first, then model updates, then UI. Run tests after each step.

---

### Pitfall 3: Over-Notification in a Two-Person Household

**What goes wrong:** With 2 users, every action by User A generates a notification for User B. Adding 5 events produces 5 notifications. The existing TSV historical import could generate hundreds. Email compounds this — partner gets spammed for routine activity.

**Why it happens:** Naive "notify on every create/update/delete" doesn't consider frequency, batching, or context. Implementing at the repository level (every DB write triggers one) instead of at the user-action level.

**How to avoid:**
- **Batch notifications:** Group changes within a 5-minute window. "Wojciech added 5 events" instead of 5 separate ones.
- **Skip self-notifications.** Never notify the actor.
- **Suppress during imports:** The historical import (TSV paste) must NOT generate notifications. Add `suppress_notifications=True` flag to batch operations.
- **Rate limit emails:** Max 1 email per 15-30 minutes, batching changes into a digest.
- **In-app first, email opt-in.** Default to activity feed only.
- **Respect `visibility` field.** Don't notify about private events.

**Warning signs:** Partner complaints about spam; email provider rate-limits you; notification badge shows hundreds after a bulk import.

**Phase to address:** Notifications phase — define notification rules BEFORE implementing triggers.

---

### Pitfall 4: Email Delivery Without Existing Infrastructure

**What goes wrong:** The app has zero email capability (no SMTP config, no provider, no email library — confirmed via `config.py` and grep). Adding email notifications means an entirely new dependency: provider account, API keys, DNS configuration (SPF/DKIM), template rendering, bounce handling, spam prevention. Disproportionate complexity for 2 users.

**Why it happens:** Email seems simple ("just send one") but involves: provider selection (Resend/SendGrid/SES), DNS setup, failure handling, templates, unsubscribe compliance, and deliverability testing.

**How to avoid:**
- **Use Resend's Python SDK** — simplest transactional email, 100 emails/day free tier (plenty for 2 users). One API call, no SMTP.
- **Start with in-app notifications only.** Defer email entirely if in-app satisfies the need.
- **Don't build email templates from scratch.** Plain text or minimal HTML wrapper. Household app, not SaaS.
- **Fire-and-forget with logging.** Never let email failure block the main request. Send in background, log failures, show in-app notification regardless.
- **Test deliverability early.** Gmail/Outlook flag unknown senders.

**Warning signs:** Emails landing in spam; email failures causing 500 errors; DNS setup taking days; partner never sees emails.

**Phase to address:** Notifications phase — decide provider upfront. Consider deferring email to follow-up if in-app suffices.

---

### Pitfall 5: Category Color Accessibility Failures on Dark Theme

**What goes wrong:** Event category colors render as dots/backgrounds on the calendar grid. With the existing dark glass-morphism UI (`bg-indigo-500/25`, `text-indigo-200`, `bg-white/[0.04]`), many colors become invisible or indistinguishable. Users with color vision deficiency (~8% of males) can't distinguish red/green categories. Small colored dots fail WCAG contrast requirements.

**Why it happens:** Colors are chosen in isolation without testing against the actual dark theme. Calendar cells use semi-transparent overlays where color math is non-trivial. Colors that work on white look different on `bg-white/[0.04]`.

**How to avoid:**
- **Curated palette only.** Provide 8-10 preset colors tested against the dark background. Don't allow arbitrary hex input.
- **Always pair color with text label or icon.** Color alone is insufficient for accessibility.
- **Test with Chrome DevTools** → Rendering → Emulate vision deficiencies.
- **Ensure 4.5:1 contrast ratio** against both `bg-indigo-500/30` (today cell) and `bg-white/[0.04]` (default cell).
- **Use Tailwind 400-weight variants:** `rose-400`, `amber-400`, `emerald-400`, `sky-400`, `violet-400`, `orange-400` — these work well on dark backgrounds.

**Warning signs:** Categories look identical on calendar; users say "I can't tell which one is which"; colored text on transparent backgrounds looks washed out.

**Phase to address:** Event categories phase — select color palette first, test against actual calendar grid before building UI.

---

### Pitfall 6: Shopping List Real-Time Sync Over-Engineering

**What goes wrong:** Both users need to see shopping list updates. The app has zero real-time infrastructure — no WebSocket, no SSE, nothing. Adding WebSocket/SSE just for shopping list introduces a new connection model, deployment complexity, reconnection logic, and a different error paradigm for one feature.

**Why it happens:** "Real-time" sounds necessary but the actual use case for 2 household users rarely requires sub-second sync. More likely: one person writes the list at home, the other checks it at the store.

**How to avoid:**
- **Don't build real-time.** For 2 users, polling or manual refresh is adequate.
- **Use HTMX polling:** `hx-trigger="every 30s"` on the shopping list container. Zero new infrastructure. Matches the existing HTMX OOB-swap pattern used throughout.
- **Optimistic UI:** When current user adds/removes items, update DOM immediately via HTMX swap. Partner gets update on next poll.
- **Add a visible "Refresh" button** as fallback.

**Warning signs:** Adding WebSocket library to requirements; writing connection lifecycle code; building reconnection logic; reverse proxy issues.

**Phase to address:** Shopping list phase — explicitly decide NO real-time before starting.

---

### Pitfall 7: Expense Category Budget Limits Creating False Alerts

**What goes wrong:** Per-category limits (e.g., "Groceries: max 2000 PLN/month") trigger alerts when exceeded. But recurring expenses (`recurring=True`, `month=0` in existing model) are shared across all months — a 500 PLN recurring "Bills" expense with a 600 PLN limit leaves only 100 PLN headroom. Seasonal variation (heating in winter) causes constant false alerts that users learn to ignore.

**Why it happens:** Static limits don't account for: recurring vs. one-time mix, seasonal variation, or the carry-forward balance system. The existing model separates recurring (month=0) from one-time (month=1-12), but category limits must aggregate both.

**How to avoid:**
- **Limits are informational, never blocking.** Show "90% of Groceries budget used" as soft warning, never prevent saving.
- **Include recurring expenses in calculations.** Sum both recurring and one-time for month + category.
- **Show limits as visual threshold lines on charts**, not alert modals.
- **Default to no limits.** Per-category limits are fully optional.
- **Implement category tagging and charts first**, add optional limits as follow-up.

**Warning signs:** Users immediately disable alerts; alerts fire on day 1 of every month from recurring expenses; limit UI more complex than expense tracking.

**Phase to address:** Expense categories phase — ship tagging + charts first, limits second.

---

### Pitfall 8: Chart Library Bloat in a Vanilla JS App

**What goes wrong:** Pie charts for expense categories seem to require Chart.js (~200KB) or D3 (~280KB). The existing app uses zero chart libraries — `budget_stats.html` renders bar charts as pure CSS/HTML divs with inline widths. Adding a chart library triples JavaScript payload and breaks the lightweight pattern.

**Why it happens:** Developers reach for Chart.js by default without checking the existing approach. For 5-10 expense categories, a full charting library is overkill.

**How to avoid:**
- **Extend existing CSS bar pattern.** Budget stats already uses `div` elements with dynamic widths and colors — this works for horizontal category bar charts.
- **For pie/donut charts, use SVG `stroke-dasharray`.** ~30 lines of vanilla JS generating `<circle>` elements — no library needed.
- **If a library is truly needed, use Chart.js (65KB gzipped)** — not D3 (85KB). But verify need first.
- **Lazy-load chart scripts only on the stats page**, never in `base.html`.

**Warning signs:** `npm install chart.js`; CDN `<script>` in base template; JS bundle >100KB; charts don't match glass-morphism aesthetic.

**Phase to address:** Expense categories phase — prototype with CSS/SVG first, add library only if insufficient.

---

## Moderate Pitfalls

### Pitfall 9: Notification Storage Growing Unbounded

**What goes wrong:** Without retention policy, notifications table grows indefinitely. 10-50 rows/week × 52 weeks = 500-2600 rows/year. Activity feed becomes an unmanageable scroll of stale items.

**How to avoid:**
- Auto-expire: delete notifications older than 30 days (Supabase `pg_cron` or application-level cleanup on read).
- Paginate the feed — show last 20, load more on scroll.
- Add `read_at` timestamp and `is_read` boolean.

**Phase to address:** Notifications phase — include retention in schema design.

---

### Pitfall 10: Shopping List String Parsing Ambiguity

**What goes wrong:** String input "milk, bread, eggs" splits to 3 items. But "mac and cheese" is 1 item, "apples and oranges" might be 2. Polish input adds complexity: "mleko, chleb i jajka" (comma + "i" as separators).

**How to avoid:**
- **Split on newlines and commas only.** Don't try "and"/"i" splitting.
- **Keep quantity as part of name string** ("2x milk" stays as "2x milk").
- **Show preview** before adding parsed items.
- **Individual add is primary path.** Bulk parse is a convenience shortcut.

**Phase to address:** Shopping list phase — define minimal parsing rules upfront.

---

### Pitfall 11: Dashboard Becoming a Maintenance Bottleneck

**What goes wrong:** Dashboard depends on every module (events, budget, notifications, shopping list). Any module change risks breaking dashboard. It becomes the most fragile page, breaking on unrelated changes.

**How to avoid:**
- **Build dashboard LAST** — it's read-only aggregation; don't let it drive other features.
- Dashboard service calls other services, not repositories directly.
- Each widget degrades gracefully — if budget load fails, show "Unavailable" instead of crashing.
- Use thin data-transfer dicts for widgets, not full model objects.

**Phase to address:** Dashboard must be the final phase.

---

### Pitfall 12: i18n Key Explosion Across 5 Features

**What goes wrong:** Each feature adds 20-40 i18n keys to `en.json`/`pl.json`. Dashboard ~15 keys, categories ~20, notifications ~15, shopping list ~10. Developers forget to add keys to both files, rendering raw key strings.

**How to avoid:**
- Add keys to BOTH `en.json` and `pl.json` in the same commit.
- Namespace: `dashboard.*`, `notification.*`, `category.*`, `shopping.*`.
- Write a test validating key parity across locale files.

**Phase to address:** All phases — enforce from the start.

---

### Pitfall 13: Category Presets vs. Custom Categories — Two Sources of Truth

**What goes wrong:** App ships preset categories (Work, Personal, Health). Users add custom ones. Presets in code + custom in database = two sources of truth. Updating preset names collides with user data.

**How to avoid:**
- **All categories in the database.** Presets are seeded on first use, not hardcoded.
- Users can rename/delete presets — they're just default starting data.
- Never identify categories by name in code. Use IDs only.
- Don't add `is_preset` flag — unnecessary complexity.

**Phase to address:** Categories phase — decide storage model before building.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Dashboard | N+1 REST queries (#1) | Parallel fetch or RPC; build last |
| Dashboard | Cross-module coupling (#11) | Service composition, graceful degradation |
| Notifications | Over-notification (#3) | Batch windows, suppress imports |
| Notifications | Email infrastructure (#4) | In-app first; Resend if email needed |
| Notifications | Unbounded storage (#9) | 30-day retention, pagination |
| Event categories | Color accessibility (#5) | Curated palette, color+text pairing |
| Event categories | Presets vs custom (#13) | All in DB, seeded not hardcoded |
| Expense categories | Schema blast radius (#2) | Nullable FK, staged rollout |
| Expense categories | False budget alerts (#7) | Soft warnings, include recurring |
| Expense categories | Chart bloat (#8) | CSS/SVG first |
| Shopping list | Over-engineered sync (#6) | HTMX polling, no WebSocket |
| Shopping list | Parsing ambiguity (#10) | Comma/newline split only |
| All features | i18n gaps (#12) | Parity test across locales |

---

## Recommended Phase Ordering (Based on Pitfall Risk)

1. **Event categories** — New table + nullable FK on events. Lowest risk, no external dependencies.
2. **Expense categories** — Same pattern as event categories. Adds charts (CSS/SVG).
3. **Shopping list** — New independent table, HTMX polling, no cross-dependencies.
4. **Notifications** — Depends on knowing what creates notifications (events, budget, shopping changes).
5. **Dashboard** — Aggregates all above. Build LAST when data sources are stable.

This ordering minimizes building on unstable foundations and keeps each phase's blast radius contained.

---

## Sources

- Direct codebase analysis: `app/database/models.py` (dataclass models, Event/Expense fields), `app/database/supabase_store.py` (synchronous httpx singleton, REST pattern), `app/events/repository.py` (mapper pattern), `app/budget/expense_repository.py` (expense queries), `app/budget/overview_service.py` (aggregation pattern)
- Existing template patterns: `budget_stats.html` (CSS bar charts, fetch-based JS), `partials/month_grid.html` (event display, dark theme classes)
- Existing config: `config.py` (no email config present)
- Architecture: Supabase REST API via synchronous `httpx.Client` singleton, HTMX partial swaps, Tailwind prebuilt CSS
- WCAG 2.1 contrast requirements: 4.5:1 for normal text, 3:1 for large text