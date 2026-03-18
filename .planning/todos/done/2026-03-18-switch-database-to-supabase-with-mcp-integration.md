---
created: 2026-03-18T19:49:39.256Z
title: Switch database to Supabase with MCP integration
area: database
files:
  - "requirements.txt"
  - "config.py"
  - "app/database/database.py"
  - "app/database/models.py"
status: pending
priority: high
phase: "01-foundation"
---

## Problem

Phase 1 plan currently uses SQLite for the database, which is suitable for local development but not ideal for production or multi-device household calendar sync. The project has access to Supabase (PostgreSQL) which is free and already connected to the workspace.

Supabase provides:
- Managed PostgreSQL database (no infrastructure overhead)
- Built-in authentication (optional enhancement)
- Real-time subscriptions (useful for Phase 5 real-time sync)
- MCP server integration available in the workspace for table management

Current Phase 1 plan (01-01-PLAN.md) uses SQLite, but switching to Supabase would provide better scalability, especially when two users are actively syncing with Google Calendar (Phase 4).

## Solution

**Before executing Phase 1:** Update the database layer to use Supabase PostgreSQL instead of SQLite.

Steps:
1. Update `requirements.txt`: Replace sqlite3 with psycopg2 (PostgreSQL adapter)
2. Update `config.py`: Change DATABASE_URL from sqlalchemy sqlite:// to postgresql://
3. Update `app/database/database.py`: Ensure SQLAlchemy engine properly handles PostgreSQL connection pooling
4. Use MCP server in workspace to create initial tables (Supabase schema initialization)
5. Update Phase 1 plans (01-01-PLAN.md, 01-02-PLAN.md, 01-03-PLAN.md) to reflect PostgreSQL setup
6. Add `.env` example with Supabase connection string format (user, password, host, port, dbname)

**No impact on models or migration steps** — SQLAlchemy handles PostgreSQL transparently.

**Timing:** Should be done BEFORE executing Phase 1, so both Wave 1 and Wave 2 use correct database.

