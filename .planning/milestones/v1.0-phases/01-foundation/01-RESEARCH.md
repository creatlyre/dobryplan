# Phase 1 Research: Foundation

**Phase:** 01 - Foundation  
**Goal:** Enable OAuth2 authentication and establish two-user shared calendar model with persistent database schema.  
**Date:** 2026-03-18  
**Researched By:** gsd-phase-researcher (via orchestrator)

---

## Overview

Phase 1 establishes the complete foundation for CalendarPlanner: user authentication via Google OAuth2, two-user household authorization model, and the persistent database schema supporting events, users, and sync state. This phase is critical path for all subsequent work.

---

## OAuth2 Architecture (Google)

### Flow for Two-User Household Model

1. **User A signs in:**
   - Click "Login with Google"
   - Redirected to Google OAuth consent screen
   - Google returns auth code
   - Exchange code for access_token + refresh_token + user_info
   - Save tokens securely in DB (refresh_token, access_token, expiry)
   - Create or retrieve User A in database
   - Set session token (JWT) for browser
   - Redirect to calendar page

2. **User A invites User B:**
   - User A navigates to Settings → Invite Household Member
   - Enters User B's email
   - System stores invitation record (pending)
   - User B receives email with accept link (or shows on login)

3. **User B signs in:**
   - Google OAuth flow (same as User A)
   - System detects pending invitation to User B's email
   - Auto-accepts invitation
   - Links User B to existing Calendar (both users now see same events)

### Key Implementation Details

**Token Storage (THE PITFALL):**
- Store per-user: `access_token`, `refresh_token`, `token_type`, `expiry_datetime`
- Google limits to 100 refresh tokens per OAuth client per user
- **Rule:** Reuse existing refresh_token; do NOT request new token if valid one exists
- Implement error handling for `invalid_grant` (token revoked) — force re-auth
- Store tokens in encrypted column in `users` table (at a minimum: AES-256)

**Session Management:**
- Use JWT tokens for web session (issued after OAuth succeeds)
- JWT includes user_id, calendar_id (household)
- Stored in httpOnly cookie (secure, not accessible to JavaScript)
- Expiry: 8 hours access token, 7 days refresh token
- FastAPI native support via `fastapi.security.HTTPBearer` + `PyJWT`

**Multi-Device / Multi-Tab Support:**
- Session should survive browser refresh and multiple tabs
- JWT in httpOnly cookie automatically sent on all requests
- Verify cookie validity on each request (middleware)
- If expired, middleware attempts refresh (if refresh token valid)
- If refresh fails (user revoked), redirect to login

---

## Database Schema (Phase 1)

### Core Tables

**users**
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  google_id VARCHAR(255) UNIQUE,
  
  -- OAuth tokens (encrypted)
  google_access_token TEXT,
  google_refresh_token TEXT,
  google_token_expiry DATETIME,
  
  -- Household link (two-user model)
  calendar_id UUID FOREIGN KEY,  -- points to shared calendar
  
  -- Audit / tracking
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW(),
  last_login DATETIME
);
```

**calendars**
```sql
CREATE TABLE calendars (
  id UUID PRIMARY KEY,
  name VARCHAR(255),  -- e.g., "Smith Household"
  timezone VARCHAR(50) DEFAULT 'UTC',  -- user's local timezone
  
  -- Shared configuration
  owner_user_id UUID FOREIGN KEY,  -- user who created; both users have equal edit rights
  
  -- Google sync state
  google_calendar_id VARCHAR(255),  -- Google Calendar ID this syncs to
  last_sync_at DATETIME,
  
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW()
);
```

**calendar_invitations** (for two-user linking)
```sql
CREATE TABLE calendar_invitations (
  id UUID PRIMARY KEY,
  calendar_id UUID FOREIGN KEY,
  invited_email VARCHAR(255) NOT NULL,
  inviter_user_id UUID FOREIGN KEY,
  status VARCHAR(20) DEFAULT 'pending',  -- pending, accepted, rejected
  created_at DATETIME DEFAULT NOW(),
  expires_at DATETIME
);
```

**events** (minimal for Phase 1)
```sql
CREATE TABLE events (
  id UUID PRIMARY KEY,
  calendar_id UUID FOREIGN KEY,
  created_by_user_id UUID FOREIGN KEY,
  
  title VARCHAR(255) NOT NULL,
  description TEXT,
  
  -- Timezone-aware datetime
  start_at DATETIME NOT NULL,
  end_at DATETIME NOT NULL,
  timezone VARCHAR(50),  -- event's timezone (for DST safety)
  
  -- Recurrence (RFC5545 RRULE string, e.g., 'FREQ=WEEKLY;BYDAY=MO,WE,FR')
  rrule VARCHAR(500),  -- NULL means one-time event
  
  -- Audit
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW(),
  last_edited_by_user_id UUID,  -- for conflict detection (Phase 2)
  is_deleted BOOLEAN DEFAULT FALSE,  -- soft delete
  
  -- Google sync state
  google_event_id VARCHAR(255),  -- Google's event ID after sync
  google_sync_at DATETIME
);
```

**google_sync_state** (Phase 4, but schema useful to understand here)
```sql
CREATE TABLE google_sync_state (
  id UUID PRIMARY KEY,
  user_id UUID FOREIGN KEY,
  calendar_id UUID FOREIGN KEY,
  
  last_sync_token VARCHAR(255),  -- for incremental sync
  last_sync_at DATETIME,
  next_sync_at DATETIME,
  
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW()
);
```

### Indexing (Phase 1)

```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_calendar_id ON users(calendar_id);
CREATE INDEX idx_events_calendar_id ON events(calendar_id);
CREATE INDEX idx_events_start_at ON events(start_at, end_at);
```

---

## FastAPI Project Structure

```
calendarplanner/
├── main.py                    # Entry point, app initialization
├── config.py                  # Environment variables, settings
├── requirements.txt           # pip dependencies
│
├── app/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── oauth.py              # Google OAuth2 flow
│   │   ├── dependencies.py        # FastAPI dependency injection (get_current_user)
│   │   └── routes.py             # POST /auth/login, callback, logout
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py             # SQLAlchemy ORM models (User, Calendar, Event, etc.)
│   │   ├── schemas.py            # Pydantic request/response schemas
│   │   ├── database.py           # Session, engine, Base
│   │   └── migrations/           # Alembic versions (if using migrations)
│   │
│   ├── users/
│   │   ├── __init__.py
│   │   ├── service.py            # UserService: create_user, link_user_to_calendar, etc.
│   │   ├── repository.py         # UserRepository: DB queries
│   │   └── routes.py             # GET /api/users/me, POST /api/users/invite
│   │
│   ├── calendars/
│   │   ├── __init__.py
│   │   ├── service.py            # CalendarService: create, get_shared_calendar
│   │   ├── repository.py         # CalendarRepository
│   │   └── routes.py             # GET /api/calendar
│   │
│   ├── events/
│   │   ├── __init__.py
│   │   ├── service.py            # EventService (CRUD, upcoming events)
│   │   ├── repository.py         # EventRepository
│   │   └── routes.py             # (populated in later phases)
│   │
│   └── templates/
│       ├── base.html             # Jinja2 base template
│       ├── login.html            # Google OAuth button
│       ├── calendar.html         # Main calendar view (basic for Phase 1)
│       └── invite.html           # Invite form
│
├── middleware/
│   ├── __init__.py
│   └── auth_middleware.py        # Session validation, JWT verification
│
├── tests/
│   ├── __init__.py
│   ├── test_auth.py             # OAuth flow mocking, token refresh
│   ├── test_users.py            # Create user, link calendar
│   └── conftest.py              # pytest fixtures
│
└── .env.example                 # Environment variables template
```

---

## Required Dependencies (requirements.txt)

```
fastapi==0.135.1
uvicorn[standard]==0.33.0
sqlalchemy==2.0.30
alembic==1.13.1
pydantic[email]==2.5.3
python-dotenv==1.0.0

# Google OAuth2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.93.0
PyJWT==2.8.1
cryptography==41.0.7

# Frontend (Jinja2 built into Starlette/FastAPI)
Jinja2==3.1.2

# Database
sqlite3  # Built-in, no pip needed

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2

# Code quality (optional)
black==23.12.1
flake8==6.1.0
mypy==1.7.1
```

---

## Testing Strategy (Phase 1)

### Auth Tests

```python
# tests/test_auth.py
class TestOAuth2:
    def test_google_login_redirect(self):
        # GET /auth/login → redirects to Google consent screen
        pass
    
    def test_oauth_callback_creates_user(self):
        # GET /auth/callback?code=XXX → creates User in DB
        pass
    
    def test_oauth_callback_sets_session(self):
        # Session cookie set after callback
        pass
    
    def test_session_persists_on_refresh(self):
        # User reloads page → session still valid
        pass
    
    def test_refresh_token_reuse(self):
        # Do NOT request new refresh token if existing is valid
        pass
    
    def test_invalid_grant_handling(self):
        # Google returns invalid_grant → force re-auth gracefully
        pass

class TestTwoUserModel:
    def test_user_a_invites_user_b(self):
        # User A → POST /api/users/invite → email to User B
        pass
    
    def test_user_b_accepts_invitation(self):
        # User B logs in → auto-linked to Calendar A
        pass
    
    def test_both_users_see_same_calendar(self):
        # User A creates event → Query as User B returns event
        pass
```

### Database Tests

```python
# tests/test_database.py
class TestDatabaseSchema:
    def test_users_table_exists(self):
        # Check schema: id, email, calendar_id, oauth tokens
        pass
    
    def test_calendars_table_exists(self):
        # Check schema: id, name, timezone, owner, google_calendar_id
        pass
    
    def test_events_table_exists(self):
        # Check schema: id, calendar_id, created_by, start, end, rrule
        pass
    
    def test_unique_constraints(self):
        # users.email unique, users.google_id unique
        pass
    
    def test_foreign_keys(self):
        # users.calendar_id → calendars.id
        # events.calendar_id → calendars.id
        pass
```

---

## Validation Architecture (Nyquist)

### Dimension 1: Tokens & Secrets
- **Validate:** OAuth tokens are stored encrypted, never logged, never exposed in responses
- **Test:** Attempt to read tokens via API response → should get {error: unauthorized}

### Dimension 2: Session Persistence
- **Validate:** Session survives browser refresh, page reload, multiple tabs
- **Test:** Login → create event → reload page → calendar still loads (no new login needed)

### Dimension 3: Two-User Access Control
- **Validate:** User A creates event → User B can see it without explicit permission
- **Test:** User A POST /api/events → User B GET /api/events → contains A's event

### Dimension 4: Invitation Flow
- **Validate:** User can only join household they were invited to
- **Test:** Uninvited user attempts to access calendar → {error: unauthorized}

### Dimension 5: Database Integrity
- **Validate:** No orphaned events (all events linked to valid calendar_id)
- **Test:** Soft-delete user → orphaned events still queryable but marked deleted

---

## Deployment Readiness (Phase 1)

### Environment Variables

Create `.env.example`:
```
# FastAPI
DEBUG=false
SECRET_KEY=your-secret-key-here

# Google OAuth2
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
GOOGLE_SCOPES=openid,profile,email,https://www.googleapis.com/auth/calendar

# Database
DATABASE_URL=sqlite:///./calendar.db
DB_ENCRYPTION_KEY=your-encryption-key-for-oauth-tokens

# Session
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=8
```

### Entry Conditions Met After Phase 1

✓ User can sign in via Google OAuth2  
✓ Two users can be invited and linked to shared calendar  
✓ Both users see same calendar in UI  
✓ Session persists across browser refresh  
✓ Database schema supports all Phase 1-6 needs  
✓ OAuth tokens managed securely (encrypted, reused, refreshed)  

---

## Summary

Phase 1 implements the foundation: **a secure OAuth2 authentication system for two household members, a shared calendar data model, and the initial FastAPI + SQLite project structure.** All subsequent phases depend on this foundation.

Critical success factors:
1. OAuth token refresh must avoid exhaustion (reuse tokens, handle invalid_grant)
2. Session must persist reliably across page reloads
3. Two-user linking must be seamless and foolproof
4. Database schema must be flexible enough for recurring events + Google sync (Phases 3-4)

---

*Research completed: 2026-03-18*  
*Confidence: HIGH (official Google OAuth docs + FastAPI/SQLAlchemy best practices)*
