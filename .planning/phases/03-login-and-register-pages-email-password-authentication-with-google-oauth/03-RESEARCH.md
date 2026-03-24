# Phase 03: Login and Register Pages — Research

**Researched:** 2026-03-24
**Level:** 1 (Quick Verification — established patterns, confirming Supabase Auth REST API)

## Current State Analysis

### Existing Backend Auth Infrastructure (FULLY BUILT)

The following API endpoints already exist and work:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/login` | GET | Redirects to Google OAuth (Supabase or direct) |
| `/auth/callback` | GET | Handles OAuth callback, creates session |
| `/auth/session` | POST | Creates session from Supabase access token |
| `/auth/register` | POST | Email/password signup via Supabase Auth API |
| `/auth/password-login` | POST | Email/password sign-in via Supabase Auth API |
| `/auth/logout` | POST/GET | Clears cookies, redirects to `/auth/login` |

### What's MISSING (Phase 3 scope)

1. **No HTML login page** — `GET /auth/login` just redirects to Google OAuth. No form for email/password.
2. **No HTML register page** — `POST /auth/register` exists (API) but no GET handler returning a form.
3. **No forgot password flow** — No Supabase password recovery endpoint implemented.
4. **No update password page** — No callback handler for password reset links.
5. **No email verification callback** — Supabase sends confirmation emails, but no `/auth/confirm` handler.

## Technical Approach

### Architecture: Server-Rendered Jinja2 Templates + Fetch API

The app uses **FastAPI + Jinja2 templates** with **htmx** and vanilla JS fetch for forms. No frontend framework. Auth forms should follow the same pattern:

1. **GET routes** render HTML templates (login.html, register.html, forgot-password.html, update-password.html)
2. **Form submission** via `fetch()` to existing POST API endpoints
3. **Client-side validation** with inline error messages (no native `alert()`)
4. **Success/error handling** in JS — redirect on success, show error message on failure

### Supabase Auth REST API Endpoints Used

The project talks directly to Supabase Auth REST API via `httpx` (no Python SDK). Current functions in `supabase_auth.py`:
- `supabase_sign_up(email, password)` → `POST /auth/v1/signup`
- `supabase_password_sign_in(email, password)` → `POST /auth/v1/token?grant_type=password`
- `fetch_supabase_user(access_token)` → `GET /auth/v1/user`
- `refresh_supabase_access_token(refresh_token)` → `POST /auth/v1/token?grant_type=refresh_token`

**New function needed:**
- `supabase_request_password_reset(email, redirect_to)` → `POST /auth/v1/recover` with `{"email": "...", "redirect_to": "..."}`
- `supabase_update_user_password(access_token, new_password)` → `PUT /auth/v1/user` with `{"password": "..."}`

### Password Reset Flow (Supabase)

1. User clicks "Forgot password?" → submits email to `POST /auth/forgot-password`
2. Backend calls Supabase `POST /auth/v1/recover` with email + redirect URL
3. Supabase sends a magic link email with `token_hash` and `type=recovery`
4. User clicks link → redirected to `/auth/confirm?token_hash=...&type=recovery&next=/auth/update-password`
5. `/auth/confirm` route exchanges token for session, redirects to update-password page
6. User enters new password → `PUT /auth/v1/user` with Bearer token

### Email Verification Flow (Supabase)

1. User registers → Supabase auto-sends confirmation email (if email confirmations enabled)
2. Email contains link: `{SITE_URL}/auth/confirm?token_hash=...&type=signup`
3. `/auth/confirm` route handles this — exchanges token for session via Supabase
4. Redirect to `/` (dashboard) after confirmation

### Confirm Callback Route

A single `/auth/confirm` GET handler covers both signup confirmation and password recovery:

```
GET /auth/confirm?token_hash={hash}&type={signup|recovery}&next={optional_redirect}
```

Backend calls Supabase `POST /auth/v1/verify` with `{token_hash, type}` to exchange for session tokens. Then:
- `type=signup` → create session, redirect to `/`
- `type=recovery` → create session, redirect to `/auth/update-password`

### Design: Glassmorphic Dark Theme

All existing pages use:
- **Background:** `linear-gradient(135deg, #0f0c29, #1e1553, #2d2463, #1a2a6c, #0d1b4b)`
- **Cards:** `background: rgba(255,255,255,0.07); backdrop-filter: blur(24px); border: 1px solid rgba(255,255,255,0.16)`
- **Fonts:** Plus Jakarta Sans (headings), DM Sans (body)
- **Buttons:** Primary gradient `linear-gradient(135deg, rgba(99,102,241,0.82), rgba(139,92,246,0.82))`
- **Input fields:** Need glassmorphic styling matching card backgrounds
- **Colors:** Indigo/violet primary (`#a5b4fc`, `#818cf8`), cyan accent (`#67e8f9`)

### Files to Create/Modify

**New files:**
- `app/templates/login.html` — Login page template
- `app/templates/register.html` — Register page template
- `app/templates/forgot_password.html` — Forgot password page
- `app/templates/update_password.html` — Set new password page

**Modified files:**
- `app/auth/routes.py` — Add GET handlers for login, register, forgot-password, update-password, confirm
- `app/auth/supabase_auth.py` — Add password reset + update + verify token functions
- `app/middleware/auth_middleware.py` — Add new public routes
- `app/locales/en.json` — Add i18n keys for auth forms
- `app/locales/pl.json` — Add Polish translations
- `tests/test_auth.py` — Add tests for new routes

### Public Routes Required

These routes must be added to `SessionValidationMiddleware.public_routes`:
- `/auth/login` (already there)
- `/auth/register` (already there)
- `/auth/forgot-password`
- `/auth/update-password`
- `/auth/confirm`
- `/auth/logout` (already there)

### Form Validation Rules

**Login form:**
- Email: required, valid email format
- Password: required, min 6 chars (Supabase default minimum)

**Register form:**
- Email: required, valid email format
- Password: required, min 6 chars
- Confirm password: must match password

**Forgot password:**
- Email: required, valid email format

**Update password:**
- New password: required, min 6 chars
- Confirm new password: must match

### Security Considerations

- CSRF: Not needed — using `fetch()` with JSON body (not form POST to same origin)
- Rate limiting: Supabase handles rate limiting on auth endpoints
- Password strength: Supabase enforces min 6 chars server-side; client validates pre-submit
- XSS: All template variables auto-escaped by Jinja2
- Token handling: Session tokens in httpOnly cookies only
- Recovery tokens: One-time use, expire after configured period in Supabase

## Standard Stack

| Concern | Technology | Already in project? |
|---------|------------|---------------------|
| Backend | FastAPI + Jinja2 | Yes |
| Auth provider | Supabase Auth (REST API) | Yes |
| HTTP client | httpx | Yes |
| Styling | Inline Tailwind-ish + custom CSS | Yes |
| JS | Vanilla fetch() | Yes |
| i18n | Custom translate() | Yes |
| Tests | pytest + TestClient | Yes |

## Don't Hand-Roll

- Session management — use existing cookie-based session pattern
- OAuth flow — use existing Supabase OAuth redirect
- Password hashing — Supabase handles all password storage
- Email sending — Supabase sends confirmation/recovery emails

## Common Pitfalls

1. **Supabase email confirmation toggle** — If email confirmations are enabled, `supabase_sign_up` may NOT return an `access_token` (user must confirm first). The register handler already handles this case.
2. **Recovery token exchange** — Must use `POST /auth/v1/verify` (not `/auth/v1/token`) to exchange token_hash for session.
3. **Redirect URL configuration** — Supabase requires redirect URLs to be whitelisted in project settings (Dashboard → Auth → URL Configuration).
4. **Update password requires active session** — `PUT /auth/v1/user` needs a valid Bearer token from the recovery flow.

## Validation Architecture

### Observable Truths

1. User can visit `/auth/login` and see a login form with email/password fields and Google sign-in button
2. User can sign in with email/password from the login page
3. User can visit `/auth/register` and see a registration form
4. User can register with email/password
5. User can click "Forgot password?" and receive a recovery email
6. User can reset their password via recovery link
7. All auth pages match Synco's glassmorphic dark theme
8. All strings are translated (en + pl)

### Test Strategy

- Unit tests for new `supabase_auth.py` functions (mock httpx)
- Integration tests for GET routes (check 200 status, HTML content)
- Integration tests for forgot-password and confirm routes (mock Supabase API)
- Verify all i18n keys present in both locale files

---

*Research complete: 2026-03-24*
