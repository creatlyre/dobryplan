# Phase 31: Paid Self-Hosted Distribution - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning
**Source:** Auto mode (--auto) with research

<domain>
## Phase Boundary

Phase 31 delivers the paid self-hosted distribution package for Synco. This covers requirements SHS-01 through SHS-04:

- A Docker Compose production package for buyers to self-host Synco
- A license-key / purchase-token verification system so only paid customers can run the self-hosted package
- A versioned upgrade path with release notes and migration instructions
- A buyer-facing setup guide that is complete and reproducible

This phase builds directly on Phase 30's Dockerfile and Phase 29's Stripe billing infrastructure.

**What is NOT in scope:**
- SaaS/Cloud changes (Phase 30 complete)
- Stripe checkout for self-hosted purchase (that's GTM-03 in Phase 33)
- Landing page or pricing page (Phase 33)
- PWA or mobile (Phase 32)

</domain>

<decisions>
## Implementation Decisions

### License Key Verification (SHS-02) — LOCKED
- Use HMAC-based license keys signed with a server-side secret
- Key format: `SYNCO-XXXXXX-XXXXXX-XXXXXX` (base32 encoded, human-readable)
- License key verified at app startup — if `SYNCO_LICENSE_KEY` env var is set and `ENVIRONMENT=self-hosted`, validate the key's HMAC signature
- Invalid key: app starts but shows a license warning banner on every page
- No phone-home / online verification — keys are self-contained (offline-friendly)
- License key generation is a CLI tool (`python -m app.licensing.generate`) that runs on the server/admin side

### Docker Compose Package (SHS-01) — LOCKED
- `docker-compose.yml` in a new `self-hosted/` directory
- Uses the existing Dockerfile from Phase 30
- Includes: app service + Supabase (via official supabase/postgres image) + optional Caddy reverse proxy
- All config via `.env` file (template provided)
- Health checks on all services

### Upgrade Path (SHS-03) — LOCKED
- `self-hosted/UPGRADE.md` documents upgrade procedure (docker compose pull + restart)
- `self-hosted/CHANGELOG-SELFHOSTED.md` tracks self-hosted-specific release notes
- Database migrations handled by Supabase migrations (already in `supabase/migrations/`)
- Semantic versioning in `pyproject.toml` is the version reference

### Setup Guide (SHS-04) — LOCKED
- `self-hosted/README.md` — complete, step-by-step guide
- Covers: prerequisites, .env setup, docker compose up, first-user creation, Google OAuth config, Stripe config (optional for self-hosted), DNS/HTTPS via Caddy
- Troubleshooting section for common issues

### Claude's Discretion
- Exact Docker Compose service names and network configuration
- Caddy configuration details (reverse proxy + auto-HTTPS)
- License key HMAC algorithm choice (SHA256 recommended)
- Warning banner styling (should match existing glassmorphism theme)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Infrastructure (from Phase 30)
- `Dockerfile` — Production container build (multi-stage, gunicorn+uvicorn)
- `config.py` — All environment variables (Settings class)
- `.env.example` — Environment variable documentation
- `railway.toml` — Railway deployment config (reference for deploy patterns)

### Billing (from Phase 29)
- `app/billing/service.py` — Stripe checkout, webhook handler
- `app/billing/dependencies.py` — Plan entitlement checks
- `app/billing/schemas.py` — Subscription/billing models
- `app/database/models.py` — Subscription dataclass

### Licensing
- `COMMERCIAL-LICENSE.md` — Commercial license terms
- `MONETIZATION.md` — Pricing and licensing model overview
- `LICENSE` — AGPL-3.0 license

</canonical_refs>

<specifics>
## Specific Ideas

- The self-hosted package should feel like a "premium product" — not just raw Docker files
- License key verification must be lightweight — no external API calls, no database lookup
- The setup guide should be good enough that a technical user can go from zero to running in 15 minutes
- Caddy is preferred over nginx for the reverse proxy because of automatic HTTPS via Let's Encrypt

</specifics>

<deferred>
## Deferred Ideas

- Online license key management portal (future — managed via CLI for now)
- Automatic update notifications for self-hosted instances
- Telemetry/analytics for self-hosted deployments (privacy concern)
- Multi-instance license keys (one key = one deployment for v4.0)

</deferred>

---

*Phase: 31-self-hosted*
*Context gathered: 2026-03-23 via --auto mode*
