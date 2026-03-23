# Synco Self-Hosted — Upgrade Guide

How to update your Synco self-hosted installation to a new version.

## Before You Upgrade

1. **Back up your database:**
   ```bash
   docker compose exec db pg_dump -U postgres synco > backup_pre_upgrade.sql
   ```

2. **Check the changelog** for breaking changes:
   See [CHANGELOG-SELFHOSTED.md](CHANGELOG-SELFHOSTED.md)

3. **Note your current version:**
   ```bash
   docker compose exec app python -c "from main import app; print(app.version)"
   ```

## Standard Upgrade

### 1. Pull the latest images

```bash
docker compose pull
```

Or, if building from source:

```bash
docker compose build --no-cache app
```

### 2. Stop and restart services

```bash
docker compose down
docker compose up -d
```

### 3. Verify the upgrade

```bash
# Check all services are healthy
docker compose ps

# Check app health
curl -s https://your-domain.com/health | python -m json.tool
```

All services should show `healthy` or `running`.

## Database Migrations

Database migrations run automatically on startup when needed. No manual step is required for standard upgrades.

If a release requires manual migration steps, they will be documented in the [CHANGELOG-SELFHOSTED.md](CHANGELOG-SELFHOSTED.md) for that release.

## Rollback

If something goes wrong after an upgrade:

### 1. Stop services

```bash
docker compose down
```

### 2. Restore database backup

```bash
docker compose up -d db
# Wait for db to start
docker compose exec -T db psql -U postgres synco < backup_pre_upgrade.sql
```

### 3. Start the previous version

If building from source, check out the previous version tag and rebuild:

```bash
git checkout v4.0.0
docker compose build --no-cache app
docker compose up -d
```

If using published images, specify the previous tag:

```bash
# Edit docker-compose.yml to pin the previous version, then:
docker compose up -d
```

## Version History

See [CHANGELOG-SELFHOSTED.md](CHANGELOG-SELFHOSTED.md) for all releases and changes.
