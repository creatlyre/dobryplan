# Synco Self-Hosted Changelog

All notable changes to the self-hosted distribution package.

## v4.0.0 — 2026-03-23

### Initial Release

- Docker Compose production package (app + PostgreSQL + PostgREST + Caddy)
- HMAC-based license key verification (offline, no phone-home)
- Automatic HTTPS via Caddy + Let's Encrypt
- Full feature set: calendar, budget, shopping, notifications, dashboard
- Polish/English localization
- Google Calendar sync support
- Stripe billing support (optional for self-hosted)

### Prerequisites

- Docker 24+ and Docker Compose v2
- A domain name pointed to your server (for HTTPS)
- 1 GB RAM minimum, 2 GB recommended

### Known Limitations

- Single-instance deployment only (one license key = one deployment)
- No automatic update notifications (check this changelog)
