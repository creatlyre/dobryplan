# Synco Self-Hosted Setup Guide

Complete guide to deploy Synco on your own server with Docker Compose.

## Prerequisites

- **Docker 24+** and **Docker Compose v2** — [Install Docker](https://docs.docker.com/engine/install/)
- **A domain name** pointed at your server's IP (required for automatic HTTPS)
- **Firewall** open on ports **80** (HTTP) and **443** (HTTPS)
- **1 GB RAM minimum**, 2 GB recommended
- A valid **Synco license key** from [synco.app/pricing](https://synco.app/pricing)

## Quick Start

### 1. Pull the image

The production Docker image is published to GitHub Container Registry:

```bash
# TODO: Replace OWNER with the GitHub username/org
docker pull ghcr.io/OWNER/synco:latest
```

### 2. Extract the package

```bash
# Clone and use the self-hosted directory:
cd self-hosted
```

### 3. Configure environment

```bash
cp .env.template .env
```

Edit `.env` and fill in:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Random 64-character string (`openssl rand -hex 32`) |
| `DB_ENCRYPTION_KEY` | Random 64-character string (`openssl rand -hex 32`) |
| `SYNCO_LICENSE_KEY` | Your license key from purchase email |
| `POSTGRES_PASSWORD` | Strong database password |
| `PGRST_JWT_SECRET` | Random base64 secret (`openssl rand -base64 32`) |
| `SITE_DOMAIN` | Your domain (e.g., `calendar.example.com`) |

### 4. Start services

```bash
docker compose up -d
```

### 5. Wait for health checks

```bash
docker compose ps
```

All services should show `healthy` or `running`.

### 6. Open your domain

Navigate to `https://your-domain.com` and create your first user account.

## Configuration Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Application secret for sessions and tokens | `openssl rand -hex 32` |
| `DB_ENCRYPTION_KEY` | Encryption key for sensitive data at rest | `openssl rand -hex 32` |
| `SYNCO_LICENSE_KEY` | License key from your purchase | `SYNCO-xxxxxxxx-...` |
| `POSTGRES_PASSWORD` | PostgreSQL password | Strong random password |
| `PGRST_JWT_SECRET` | JWT secret for PostgREST authentication | `openssl rand -base64 32` |
| `SITE_DOMAIN` | Your domain name for HTTPS | `calendar.example.com` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (for Calendar sync) | — |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | — |
| `GOOGLE_REDIRECT_URI` | OAuth redirect URI | `https://your-domain.com/auth/callback` |
| `STRIPE_SECRET_KEY` | Stripe secret (if billing enabled) | — |
| `SMTP_HOST` | SMTP server for email notifications | — |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username | — |
| `SMTP_PASSWORD` | SMTP password | — |
| `SMTP_FROM_ADDRESS` | Sender email address | — |
| `SENTRY_DSN` | Sentry error tracking DSN | — |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (`text` or `json`) | `json` |
| `WEB_CONCURRENCY` | Number of worker processes | `3` |

## Google Calendar Integration (Optional)

To enable Google Calendar sync:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use an existing one)
3. Enable the **Google Calendar API**
4. Create **OAuth 2.0 credentials** (Web application type)
5. Set the authorized redirect URI to: `https://your-domain.com/auth/callback`
6. Add to your `.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-secret
   GOOGLE_REDIRECT_URI=https://your-domain.com/auth/callback
   ```
7. Restart: `docker compose restart app`

## Email Notifications (Optional)

To enable email notifications, configure SMTP in your `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_ADDRESS=your-email@gmail.com
SMTP_USE_TLS=true
```

Then restart: `docker compose restart app`

## HTTPS / Custom Domain

Caddy handles HTTPS automatically using Let's Encrypt. Just set `SITE_DOMAIN` in your `.env` to your domain name (pointed at your server).

- **First startup** may take a minute to obtain the certificate.
- Caddy renews certificates automatically before expiry.
- If using `localhost` for testing, Caddy will use a self-signed certificate.

## Backup & Restore

### Create a backup

```bash
docker compose exec db pg_dump -U postgres synco > backup_$(date +%Y%m%d).sql
```

### Restore from backup

```bash
docker compose exec -T db psql -U postgres synco < backup_20260323.sql
```

### Automated backups (optional)

Add a cron job:

```bash
crontab -e
# Add: daily backup at 2 AM
0 2 * * * cd /path/to/self-hosted && docker compose exec -T db pg_dump -U postgres synco > /backups/synco_$(date +\%Y\%m\%d).sql
```

## Architecture

```
┌─────────┐     ┌──────────┐     ┌──────────────┐     ┌────────────┐
│  Caddy   │────▶│  Synco   │────▶│  PostgREST   │────▶│ PostgreSQL │
│ :80/:443 │     │   App    │     │   REST API   │     │     DB     │
└─────────┘     └──────────┘     └──────────────┘     └────────────┘
```

- **Caddy** — Reverse proxy with automatic HTTPS
- **Synco App** — FastAPI application (gunicorn + uvicorn workers)
- **PostgREST** — Supabase-compatible REST API layer
- **PostgreSQL** — Database (supabase/postgres image)

## Troubleshooting

### Port conflicts

If ports 80 or 443 are already in use:

```bash
# Check what's using the ports
sudo lsof -i :80
sudo lsof -i :443
```

Stop the conflicting service or change ports in `docker-compose.yml`.

### License key errors

If you see a red banner at the bottom of the page:

1. Verify your license key in `.env` matches the one from your purchase email
2. Ensure `SYNCO_LICENSE_KEY` has no extra spaces or quotes
3. Restart: `docker compose restart app`

### Database connection issues

```bash
# Check database logs
docker compose logs db

# Check if database is healthy
docker compose exec db pg_isready -U postgres
```

### Container won't start

```bash
# View logs
docker compose logs app

# Common fix: rebuild
docker compose build --no-cache app
docker compose up -d
```

### Google OAuth redirect mismatch

Ensure `GOOGLE_REDIRECT_URI` in your `.env` matches the authorized redirect URI in Google Cloud Console exactly (including `https://`).

## Support

- **Email:** licensing@synco.app
- **Documentation:** [synco.app/docs](https://synco.app/docs)
- **Changelog:** See [CHANGELOG-SELFHOSTED.md](CHANGELOG-SELFHOSTED.md)
