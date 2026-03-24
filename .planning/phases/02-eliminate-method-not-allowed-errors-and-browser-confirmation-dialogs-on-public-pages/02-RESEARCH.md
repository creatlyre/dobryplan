# Phase 2 Research: Eliminate Method Not Allowed Errors and Browser Confirmation Dialogs

**Completed:** 2026-03-24
**Discovery Level:** 1 — Quick Verification (all patterns established in codebase)

---

## Problem Analysis

### Issue 1: Method Not Allowed (405) Errors

**Root cause:** `SessionValidationMiddleware` in `app/middleware/auth_middleware.py` redirects unauthenticated requests using `status_code=307` (Temporary Redirect). HTTP 307 preserves the original HTTP method. When a POST/PUT/DELETE request hits any non-public route without auth, it gets redirected as POST/PUT/DELETE to `/auth/login`, which only has a `@router.get("/login")` handler → **405 Method Not Allowed**.

**Same issue in:** `auth_redirect_handler` in `main.py` (line ~258) also uses `status_code=307` for redirecting 401s on `/invite` and `/dashboard`.

**Affected code locations:**
- `app/middleware/auth_middleware.py` line 38: `return RedirectResponse(url="/auth/login", status_code=307)`
- `main.py` line ~258: `return RedirectResponse(url="/auth/login", status_code=307)`

**Fix:** Change `307` to `302` (which converts the method to GET upon redirect per RFC 7231). This is the standard pattern for auth redirects.

### Issue 2: Browser Confirmation Dialogs on Public Pages

**Root cause:** The logout button in `base.html` (line 96) uses `<form method="post" action="/auth/logout">`. When submitted, the browser stores a POST entry in its navigation history. After the POST → 303 redirect → `/auth/login`, if the user presses the browser Back button, the browser shows "Confirm Form Resubmission" dialog.

**Secondary causes:**
- The pricing page (`pricing.html`) uses native `alert()` calls for error feedback (lines 229, 235) rather than inline UI messages. While `alert()` is technically a "dialog," these are error feedback, not confirmation dialogs.

**Fix for logout:** Replace the `<form method="post">` with an `<a href="/auth/logout">` link. The GET `/auth/logout` handler already exists and works identically to the POST handler (both delete cookies and redirect to login). This eliminates the POST from browser history entirely.

**Fix for alert() on pricing:** Replace native `alert()` calls with inline toast/error messages consistent with the app's existing toast pattern (`#global-toast` in base.html).

### Issue 3: Native confirm() and alert() Calls (Authenticated Pages)

While the phase specifically targets "public pages," the codebase also uses native `confirm()` in authenticated pages:
- `budget_expenses.html` line 741: Delete-all confirmation
- `shopping.html` line 350: Clear list confirmation  
- `calendar.html` line 551: Discard unsaved changes
- `calendar.html` line 742: Delete event confirmation

And native `alert()` in authenticated pages:
- `base.html` lines 786-788, 814, 821: Quick-add validation/errors
- `billing_settings.html` lines 138, 143, 163, 167: Billing errors
- `calendar.html` line 748: Delete failed

**These are out of scope for Phase 2** (authenticated pages, not public). Could be addressed in a future UX polish phase.

---

## Validation Architecture

### Testable Behaviors

| # | Behavior | Test Type | Automated |
|---|----------|-----------|-----------|
| 1 | Middleware redirects unauthenticated POST requests as GET (302 not 307) | Integration | `pytest tests/test_security.py -k middleware` |
| 2 | Exception handler redirects unauthenticated POST requests as GET (302 not 307) | Integration | `pytest tests/test_auth.py -k redirect` |
| 3 | Logout button uses GET `<a>` link, not POST `<form>` | Unit (template check) | `grep` assertion |
| 4 | Pricing page shows inline errors, not `alert()` | Unit (template check) | `grep` assertion |
| 5 | All public pages render without errors | Integration | `pytest tests/test_go_to_market.py` |

### Existing Test Coverage

- `tests/test_auth.py` — has `test_logout_post_redirects_to_login`, `test_logout_get_redirects_to_login`, `test_invalid_session_redirects`
- `tests/test_security.py` — middleware and security header tests
- `tests/test_go_to_market.py` — landing, pricing, terms, privacy, refund page tests

---

## Technical Approach

### Standard Stack (no new dependencies)

All fixes use existing FastAPI patterns and vanilla JS. No new libraries needed.

### Architecture

No architectural changes. This is a targeted bug-fix phase touching:
1. `app/middleware/auth_middleware.py` — one-line fix (307 → 302)
2. `main.py` — one-line fix (307 → 302)
3. `app/templates/base.html` — replace logout form with link
4. `app/templates/pricing.html` — replace alert() with inline error display
5. Tests — add/update for the new behaviors

### Common Pitfalls

- **307 vs 302 vs 303:** Use 302 for middleware (generic redirect), 303 for POST-to-GET (explicit method switch). Both work for the auth redirect case; 302 is the most common convention.
- **GET logout security:** GET `/auth/logout` is already implemented. The only risk is accidental logout via prefetch, but major apps (GitHub, etc.) use GET logout links. The risk is minimal and the UX benefit (no resubmission dialogs) outweighs it.
- **Toast pattern:** `base.html` already has a `#global-toast` element. Reuse this pattern for pricing error feedback.

---

## Don't Hand-Roll

Nothing to hand-roll. All fixes use standard HTTP semantics and existing codebase patterns.

---

## Scope Summary

| Change | Files | Effort |
|--------|-------|--------|
| Fix 307 → 302 in middleware | 1 file (auth_middleware.py) | Trivial |
| Fix 307 → 302 in exception handler | 1 file (main.py) | Trivial |
| Logout: form → link | 1 file (base.html) | Small |
| Pricing: alert → toast | 1 file (pricing.html) | Small |
| Tests | 1-2 test files | Small |

**Total:** ~15-20 min Claude execution time. Single plan, 2 tasks.
