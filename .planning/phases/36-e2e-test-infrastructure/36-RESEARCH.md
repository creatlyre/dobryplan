# Phase 36: E2E Test Infrastructure — Research

**Researched:** 2026-03-25
**Level:** 2 (Standard Research — new library, established patterns)

## Standard Stack

- **Playwright** (`@playwright/test`) — Node.js E2E testing framework
- **Setup projects** — Playwright's `dependencies` feature for auth setup before test projects
- **Storage state** — JSON files with cookies/localStorage saved after login, reused across tests
- **GitHub Actions** — CI runner with Playwright's official patterns

## Architecture Patterns

### Authentication via Setup Projects (Recommended)

Playwright's modern approach uses "setup projects" rather than `globalSetup` scripts. Each setup project is a normal test file matching a pattern (e.g., `*.setup.ts`) that runs before dependent projects.

**Why setup projects over globalSetup:**
- Setup projects produce traces and screenshots on failure (globalSetup doesn't)
- Setup projects can be parallelized
- Each role can have its own setup file
- Built-in dependency graph via `dependencies: ['setup']`

### Multi-Role Auth Pattern

Three Playwright projects for authenticated testing (`free`, `pro`, `family-plus`), each with:
1. A setup project that logs in and saves storage state
2. The test project that uses the saved storage state

**Login flow (from codebase analysis):**
1. Navigate to `/auth/login`
2. Fill `#email` input with email
3. Fill `#password` input with password
4. Click submit button (`.btn-primary` / form submit)
5. Login form POSTs JSON `{email, password}` to `/auth/password-login` via fetch
6. On success, `window.location.href = '/'` — redirects to dashboard
7. Server sets `session` cookie (httpOnly) and optionally `supabase_refresh` cookie

**Wait strategy:** After form submit, `await page.waitForURL('**/') ` — wait for redirect to root (dashboard).

### Project Configuration Structure

```
playwright.config.ts
├── setup-free (testMatch: **/auth.setup.ts, project: free env vars)
├── setup-pro (testMatch: **/auth.setup.ts, project: pro env vars)  
├── setup-family-plus (testMatch: **/auth.setup.ts, project: family-plus env vars)
├── free (depends: setup-free, storageState: .auth/free.json)
├── pro (depends: setup-pro, storageState: .auth/pro.json)
└── family-plus (depends: setup-family-plus, storageState: .auth/family-plus.json)
```

**Simpler alternative (recommended):** Single setup file with 3 setup tests:

```
playwright.config.ts
├── setup (testMatch: **/auth.setup.ts — runs all 3 logins)
├── free (depends: setup, storageState: playwright/.auth/free.json)
├── pro (depends: setup, storageState: playwright/.auth/pro.json)
└── family-plus (depends: setup, storageState: playwright/.auth/family-plus.json)
```

### Directory Structure

```
e2e/
├── playwright.config.ts
├── auth.setup.ts          # Login all 3 accounts, save storage state
├── tests/                 # Test files (phases 37-39)
│   └── smoke.spec.ts      # Infrastructure smoke test
└── playwright/
    └── .auth/             # Generated storage state files (gitignored)
        ├── free.json
        ├── pro.json
        └── family-plus.json
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `E2E_BASE_URL` | Target app URL | `https://synco-production-e9da.up.railway.app` |
| `E2E_FREE_EMAIL` | Free account email | (required) |
| `E2E_FREE_PASSWORD` | Free account password | (required) |
| `E2E_PRO_EMAIL` | Pro account email | (required) |
| `E2E_PRO_PASSWORD` | Pro account password | (required) |
| `E2E_FAMILY_PLUS_EMAIL` | Family+ account email | (required) |
| `E2E_FAMILY_PLUS_PASSWORD` | Family+ account password | (required) |

## Don't Hand-Roll

- **Auth session injection** — Use Playwright's storage state mechanism, not manual cookie injection
- **Custom test runner** — Use `@playwright/test` runner, not Jest or Mocha with Playwright
- **Screenshot management** — Use Playwright's built-in `screenshot: 'only-on-failure'` and trace `retain-on-failure`
- **Retry logic** — Use Playwright's built-in `retries: 1` config, not manual retry wrappers

## Common Pitfalls

1. **Storage state directory not gitignored** — `.auth/` files contain session tokens; must be in `.gitignore`
2. **Login race condition** — Must `waitForURL` after form submit, not just click; the fetch-based login in this app redirects via `window.location.href`
3. **Cookie httpOnly** — The `session` cookie is httpOnly, so JavaScript can't read it, but Playwright captures it automatically via storage state
4. **CI browser install** — Must run `npx playwright install --with-deps` in CI (installs Chromium + OS deps)
5. **Timeout too tight for network** — Tests hit Railway over the internet; 30s per test is appropriate, but `navigationTimeout` should be generous (15s)
6. **Form submission is fetch-based** — The login form uses `fetch()` to POST JSON, then `window.location.href = '/'` on success. Playwright needs to wait for the navigation, not just the fetch response.

## Validation Architecture

### Observable Truths
1. `npx playwright test` runs successfully against the live app
2. Three authenticated storage states are created (free, pro, family-plus)
3. Each storage state contains valid session cookies
4. Failed tests produce screenshots and traces
5. CI workflow runs headless on PR

### Key Links
- `auth.setup.ts` → `/auth/login` page → `/auth/password-login` API → storage state files
- `playwright.config.ts` → setup project → test projects (dependency chain)
- `.github/workflows/e2e.yml` → `npx playwright install` → `npx playwright test`

### Verification Commands
```bash
# Local: Run all tests
npx playwright test

# Local: Run only setup (auth)
npx playwright test --project=setup

# Local: Run smoke test for one role
npx playwright test --project=free smoke.spec.ts

# Check storage state was created
test -f e2e/playwright/.auth/free.json && echo "OK"

# CI: Verify workflow file
cat .github/workflows/e2e.yml | grep "playwright test"
```

---

*Research completed: 2026-03-25*
*Sources: Playwright official docs (v1.51+), codebase analysis of auth flow*
