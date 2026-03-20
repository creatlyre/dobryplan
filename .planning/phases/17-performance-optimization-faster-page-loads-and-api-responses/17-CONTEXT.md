# Phase 17: Performance Optimization - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Optimize page load times and API response performance across the CalendarPlanner app. Focus on measurable improvements: reduce external CDN dependency weight, reduce per-request overhead in the data layer, and add HTTP caching where appropriate. No feature changes — pure performance and infrastructure work.

</domain>

<decisions>
## Implementation Decisions

### CDN & Asset Loading
- Replace Tailwind CDN play script (~300KB runtime) with a prebuilt CSS file using Tailwind CLI
- Self-host the built CSS as a static file to eliminate CDN round-trip
- Keep HTMX CDN for calendar page (small, single-use) — no change needed

### Database Layer Optimization
- Reuse httpx.Client across requests via a module-level or singleton SupabaseStore instead of creating new instances per request
- Use httpx connection pooling (keep-alive) to reduce TCP/TLS overhead to Supabase
- Overview service: batch or parallelize the 4 sequential Supabase queries where possible

### HTTP Caching
- Add Cache-Control headers to static assets (CSS, locale files if served)
- API responses remain no-cache (dynamic, user-specific data)

### Claude's Discretion
- Exact Tailwind CLI build configuration
- Whether to use async httpx for parallelization or keep sync with connection pooling
- Static file serving setup (FastAPI StaticFiles mount)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/database/supabase_store.py` — SupabaseStore with httpx.Client per-operation
- `app/database/database.py` — `get_db()` yields new SupabaseStore per request
- `app/templates/base.html` — loads `cdn.tailwindcss.com` script
- `app/templates/calendar.html` — loads htmx from unpkg CDN

### Established Patterns
- All CSS uses Tailwind utility classes + custom `.glass-*` classes in base.html `<style>`
- All API calls from JS frontends use `fetch()` with JSON responses
- Templates use Jinja2 with `{{ t('key') }}` i18n helper

### Key Metrics (Current)
- base.html: 12.5 KB with inline `<style>` block for glass morphism CSS
- calendar.html: 62.7 KB (largest template)
- Tailwind CDN: ~300KB JS payload parsed on every page load
- 4 Supabase queries per overview page load (settings, hours, earnings, expenses)
- New httpx.Client created per Supabase query (no connection pooling)

</code_context>

<specifics>
## Specific Ideas

- Tailwind CLI standalone binary can build to a single CSS file
- httpx.Client supports connection pooling natively when reused
- FastAPI's StaticFiles middleware can serve the built CSS

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>
