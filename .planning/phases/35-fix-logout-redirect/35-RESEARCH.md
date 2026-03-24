# Phase 35: Fix Logout Redirect — Research

**Researched:** 2026-03-24
**Discovery Level:** 0 (pure internal fix, established patterns)

## Problem

The logout endpoint `POST /auth/logout` in `app/auth/routes.py` (line 354) returns a JSON dict:
```python
return {"message": _msg(request, "auth.logged_out")}
```

The logout form in `app/templates/base.html` (line 94) submits via `<form method="post">`, so the browser navigates to the endpoint and renders the raw JSON response `{"message":"Wylogowano"}`.

## Root Cause

The logout endpoint was written as an API-style JSON endpoint but is called from an HTML form submission (not AJAX). When a browser submits a form, it navigates to the response — showing raw JSON.

## Fix

Replace the JSON return with a `RedirectResponse` to `/auth/login` (the login page). FastAPI's `RedirectResponse` already imported in the file. Cookies can be deleted on the redirect response.

**Pattern already established:** The auth middleware at `app/middleware/auth_middleware.py:39` already redirects unauthenticated users to `/auth/login` using `RedirectResponse(url="/auth/login", status_code=307)`.

For the logout redirect, use status code `303` (See Other) — the correct HTTP status for POST-redirect-GET pattern (PRG).

## Files Involved

| File | Change |
|------|--------|
| `app/auth/routes.py` | Change `logout()` return from JSON dict to `RedirectResponse` |
| `tests/test_auth.py` | Add test for logout redirect behavior |

## Existing Test Coverage

No existing test for logout endpoint in `tests/test_auth.py`. A test should verify:
1. Session cookie is deleted after logout
2. Response is a redirect (status 303) to `/auth/login`

## Validation Architecture

**Behavior:** POST `/auth/logout` → clears cookies → 303 redirect to `/auth/login`
**Test:** `pytest tests/test_auth.py -k test_logout` exits 0
**Manual:** Click logout button → browser shows login page, not JSON
