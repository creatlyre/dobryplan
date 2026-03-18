# 01-02 Summary

## Objective
Implemented OAuth2 + JWT authentication flow with session validation middleware.

## What Was Built
- Added token encryption/decryption helpers using Fernet.
- Added Google OAuth helper functions:
  - authorization URL generation
  - auth code exchange
  - refresh token flow
- Implemented auth routes:
  - GET /auth/login
  - GET /auth/callback
  - POST /auth/logout
- Added JWT cookie session creation in OAuth callback.
- Added get_current_user dependency for protected routes.
- Added global session middleware redirecting unauthenticated users to login.

## Files Created/Updated
- app/auth/__init__.py
- app/auth/utils.py
- app/auth/oauth.py
- app/auth/dependencies.py
- app/auth/routes.py
- app/middleware/__init__.py
- app/middleware/auth_middleware.py
- main.py

## Verification
- Auth and middleware module imports pass.
- JWT and dependency flows validated through integration tests.
- Unauthenticated requests to protected route redirect to /auth/login.

## Notes
- OAuth callback also triggers auto-accept of pending household invitations for phase integration with 01-03.
- Cookie configured httpOnly + samesite=lax.
