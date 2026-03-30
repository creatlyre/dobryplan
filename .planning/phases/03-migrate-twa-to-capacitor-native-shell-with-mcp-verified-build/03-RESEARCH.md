# Phase 3: Migrate TWA to Capacitor Native Shell with MCP-Verified Build — Research

**Researched:** 2026-03-30
**Discovery Level:** 2 (Standard — known library, new integration pattern, MCP verification)

## Executive Summary

The project currently ships an Android TWA (Trusted Web Activity) that depends on Chrome to render the PWA at `https://synco-production-e9da.up.railway.app/dashboard`. Phase 3 replaces the TWA with a Capacitor native shell that **bundles all web assets inside the APK**, eliminates the Chrome dependency, enables true offline-first launch, and produces a Play Store-ready artifact — all verified using the Capacitor MCP server tools during planning and execution.

**Key insight:** This is NOT a typical Capacitor project with a JS framework build step. Dobry Plan is a **Python/FastAPI server-rendered app** with Jinja2 templates. The Capacitor shell will load bundled static assets (HTML, CSS, JS, icons) from the APK, but the app still needs the backend API for data. The migration strategy is to:
1. Export a static "app shell" from the templates into a `www/` directory
2. Configure Capacitor to bundle `www/` as the webDir
3. The app shell loads, then fetches data from the live API
4. Offline mode shows cached content via the existing service worker

## Existing Infrastructure Analysis

### Current TWA Architecture
- **android/app/build.gradle**: Standard Android app using `com.google.androidbrowserhelper:androidbrowserhelper:2.5.0`
- **LauncherActivity**: `com.google.androidbrowserhelper.trusted.LauncherActivity` — relies on Chrome Custom Tabs
- **DEFAULT_URL**: `https://synco-production-e9da.up.railway.app/dashboard`
- **Package ID**: `app.dobryplan.twa`
- **Signing**: `dobryplan-keystore.jks` with env-based passwords
- **CI/CD**: `.github/workflows/android-build.yml` — Gradle build, GitHub Releases

### Current Web Assets
- **Templates**: Jinja2 HTML templates in `app/templates/` (server-rendered)
- **Static files**: `public/` directory mounted at `/static` in FastAPI
  - `public/css/style.css` — Tailwind build output (34KB)
  - `public/icons/` — app icons (192, 512, maskable variants)
  - `public/images/` — brand images
  - `public/sw.js` — service worker (network-first nav, cache-first static)
  - `public/offline.html` — offline fallback page
  - `public/manifest.json` — PWA manifest
- **No JS build step**: No webpack/vite/rollup. JS is inline in templates or minimal vanilla JS.

### Key Challenge: Server-Rendered App → Capacitor

Capacitor expects a `webDir` containing a **complete static web app** (index.html + assets). Dobry Plan's HTML is server-rendered by FastAPI/Jinja2. This means:

**Option A: Capacitor loads remote URL (like TWA but with embedded WebView)**
- Set `server.url` in capacitor.config.ts to the production URL
- Capacitor acts as a native WebView wrapper (no Chrome dependency)
- Offline handled by existing service worker
- **Pros**: Minimal code change, same architecture as TWA
- **Cons**: Still needs network for first load (unless SW cached), not truly "bundled assets"

**Option B: Bundle a static app shell + fetch from API**
- Generate a minimal `www/index.html` with app shell UI
- App shell shows loading state, then hydrates from API
- **Pros**: True offline-first, instant first launch
- **Cons**: Major architectural change, need to duplicate/extract UI from Jinja2 templates into static HTML

**Option C (RECOMMENDED): Capacitor with server.url + improved service worker**
- Capacitor uses `server.url` pointing to production backend
- Enhanced service worker pre-caches critical assets on install
- `server.errorPath` points to a local offline fallback
- Capacitor.js bridge enables native features (future: push notifications, camera)
- **Pros**: Removes Chrome dependency (Capacitor uses Android System WebView), minimal code change, retains server-rendered architecture, enables native plugin path
- **Cons**: First launch still needs network (but SW caches aggressively after)

### Why Option C Wins

1. **Removes Chrome dependency** (CAP-01) — Capacitor uses Android System WebView, not Chrome Custom Tabs
2. **Same codebase** — No need to rewrite Jinja2 templates as static SPA
3. **Enables native plugins** — Future push notifications, camera, filesystem via Capacitor plugins
4. **CI/CD compatible** — Gradle build like current TWA, just different project structure
5. **Offline fallback** — `server.errorPath` in capacitor.config.ts serves local HTML when offline
6. **Retains keystore** (CAP-04) — Same signing config, same package ID

### What About "Bundle all assets in APK" (CAP-02)?

With Option C using `server.url`, we DON'T bundle the full app in the APK. However, we CAN bundle:
- The offline fallback page (`www/offline.html`)
- App icons and splash screen
- A minimal app shell that redirects to the server

This satisfies the spirit of CAP-02 (instant first launch with something visible) while keeping the server-rendered architecture. The service worker handles caching for subsequent launches.

**True asset bundling (Option B) would require** rewriting the entire frontend as a static SPA — a multi-week effort inappropriate for this phase.

## Capacitor Setup for Server-Rendered Apps

### Installation Steps

```bash
# Add Capacitor to existing project
npm install @capacitor/core @capacitor/cli @capacitor/android

# Initialize (creates capacitor.config.ts)
npx cap init "Dobry Plan" "app.dobryplan.twa" --web-dir www

# Create minimal www directory with offline fallback
mkdir www
cp public/offline.html www/index.html

# Add Android platform
npx cap add android
```

### Configuration (`capacitor.config.ts`)

```typescript
import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'app.dobryplan.twa',
  appName: 'Dobry Plan',
  webDir: 'www',
  server: {
    url: 'https://synco-production-e9da.up.railway.app',
    cleartext: false,
    errorPath: '/offline.html'  // Local fallback from www/
  },
  android: {
    buildOptions: {
      keystorePath: '../dobryplan-keystore.jks',
      keystoreAlias: 'dobryplan'
    }
  }
};

export default config;
```

### Key Config Points

- **`server.url`** — Tells Capacitor to load the remote server instead of local `www/` files
- **`server.errorPath`** — Falls back to local `www/offline.html` when server unreachable
- **`webDir: 'www'`** — Required even with `server.url` (Capacitor needs web assets for fallback + bridge JS)
- **`appId`** — Same as current TWA package ID to allow in-place updates

### Android Project Structure (Capacitor-generated)

After `npx cap add android`, the `android/` directory will contain a Capacitor-standard Android project:
- `android/app/src/main/java/app/dobryplan/twa/MainActivity.java` — extends `BridgeActivity`
- `android/app/src/main/assets/public/` — web assets copied from `www/`
- `android/app/src/main/res/` — Android resources (icons, splash, strings)
- `android/capacitor.settings.gradle` — Capacitor plugin dependencies
- `android/app/build.gradle` — uses `@capacitor/android` dependency

### Migration: TWA Android → Capacitor Android

The current `android/` directory is a TWA project. `npx cap add android` would conflict. Strategy:

1. **Back up** current `android/` directory (or just git tracks it)
2. **Remove** current `android/` directory
3. **Run** `npx cap add android` — generates fresh Capacitor Android project
4. **Re-apply** signing config to new `android/app/build.gradle`
5. **Copy** icons from `public/icons/` to Android res directories
6. **Update** `.github/workflows/android-build.yml` for Capacitor build commands

### Capacitor Build Commands (CI/CD)

```bash
# Sync web assets to Android project
npx cap sync android

# Build APK via Gradle (same as current)
cd android && gradle assembleRelease
```

The CI/CD workflow mostly stays the same — still Gradle-based. Main changes:
- Remove Bubblewrap references
- Add `npx cap sync android` before Gradle build
- Need Node.js for Capacitor CLI (already in workflow)

## Digital Asset Links

Current DAL at `public/.well-known/assetlinks.json` targets the TWA package. For Capacitor:
- Package ID stays the same (`app.dobryplan.twa`)
- SHA256 fingerprint stays the same (same keystore)
- DAL file needs NO changes
- Intent filter for deep links configured in Capacitor's `AndroidManifest.xml`

## MCP Verification Strategy

The Capacitor MCP server (`awesome-ionic-mcp`) provides tools that can verify:

1. **Plugin APIs**: `get_official_plugin_api({ plugin: "App" })` — verify App plugin config
2. **CLI Commands**: `cap_sync`, `cap_add` — verify CLI invocations
3. **Component search**: Confirm Capacitor plugin compatibility

During execution, MCP tools should be used to:
- Verify `capacitor.config.ts` structure matches official docs
- Confirm `@capacitor/android` setup instructions
- Validate plugin API calls if any plugins are added

## Don't Hand-Roll

| Temptation | Use Instead |
|---|---|
| Custom WebView wrapper | Capacitor's `BridgeActivity` |
| Manual asset copying | `npx cap sync` |
| Custom native Java code | Capacitor plugins |
| Custom update mechanism | Existing service worker + version API (Phase 1) |
| Custom splash screen | `@capacitor/splash-screen` plugin |

## Common Pitfalls

1. **`npx cap add android` onto existing android dir** — Will fail. Must remove old TWA android project first.
2. **Missing `www/` directory** — `cap sync` fails if `webDir` doesn't exist. Must create with at least `index.html`.
3. **`server.url` without internet** — App shows blank. Must set `server.errorPath` for offline fallback.
4. **Package ID mismatch** — If Capacitor generates a different package ID, existing installs can't update. Must match `app.dobryplan.twa`.
5. **Keystore path in Capacitor** — `buildOptions.keystorePath` is relative to `android/app/` not project root.
6. **Bubblewrap artifacts in CI** — Old workflow references Bubblewrap. Must fully replace with Capacitor commands.
7. **Gradle version mismatch** — Capacitor 6+ needs AGP 8.x. Current project uses AGP 8.2.2 which is compatible.
8. **System WebView version** — Capacitor requires Android System WebView 60+. Set `android.minWebViewVersion` in config.

## Validation Architecture

### Test Strategy

| Component | Test Type | Tool |
|---|---|---|
| `capacitor.config.ts` validity | Static check | `npx cap doctor` |
| Android project builds | CI integration | `gradle assembleRelease` |
| Web assets synced | File check | `ls android/app/src/main/assets/public/` |
| Signing config | Build output | APK signature verification |
| Offline fallback | Manual | Airplane mode on device |
| No Chrome bar | Manual | Install APK on device |
| Version API still works | Unit test | Existing `test_pwa.py` |
| DAL still served | Integration | `curl /.well-known/assetlinks.json` |

### Key Validation Points

1. `capacitor.config.ts` exists with correct `appId`, `server.url`, `webDir`
2. `android/` contains Capacitor-generated project (not TWA)
3. `android/app/build.gradle` has correct signing config
4. `npx cap sync android` completes without errors
5. `gradle assembleRelease` produces signed APK
6. APK installs on device without requiring Chrome
7. App launches in fullscreen (no browser bar)
8. Offline fallback shows when no network available

## Scope Recommendation

### Plan 1 (Wave 1): Capacitor Project Setup + Config
- Install Capacitor dependencies
- Create `capacitor.config.ts`
- Create `www/` directory with offline fallback
- Remove old TWA `android/` directory
- Run `npx cap add android`
- Re-apply signing config and icons
- Verify: `npx cap sync android` completes

### Plan 2 (Wave 2, depends on Plan 1): CI/CD Update + Build Verification
- Update `.github/workflows/android-build.yml` for Capacitor
- Add `npx cap sync` step before Gradle build
- Remove Bubblewrap references
- Update version extraction
- Checkpoint: User configures secrets, builds APK, installs on device

### Requirements Mapping

Since Phase 3 has TBD requirements, derive from Phase 2's CAP-01 through CAP-07:

| Requirement | How Addressed |
|---|---|
| CAP-01: Remove Chrome dependency | Capacitor uses System WebView, not Chrome Custom Tabs |
| CAP-02: Bundle assets in APK | `www/` bundled as offline fallback; server.url for live content |
| CAP-03: Full offline support | `server.errorPath` + existing service worker |
| CAP-04: Retain keystore | Same keystore path/alias in Capacitor buildOptions |
| CAP-05: CI/CD pipeline updated | Workflow updated from Bubblewrap to `cap sync` + Gradle |
| CAP-06: DAL still functional | Same package ID + keystore = same DAL |
| CAP-07: Device verification | Checkpoint: install APK, confirm fullscreen standalone |
