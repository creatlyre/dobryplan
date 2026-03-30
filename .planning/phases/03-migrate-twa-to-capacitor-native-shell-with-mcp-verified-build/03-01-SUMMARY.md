---
phase: 03-migrate-twa-to-capacitor-native-shell-with-mcp-verified-build
plan: 01
subsystem: android
tags: [capacitor, android, webview, offline, signing]

requires:
  - phase: none
    provides: existing TWA android project and signing keystore

provides:
  - Capacitor Android shell replacing TWA (BridgeActivity instead of LauncherActivity)
  - capacitor.config.ts with server.url pointing to production backend
  - www/ directory with offline fallback page
  - Signing config using same keystore and package ID (app.dobryplan.twa)
  - Brand colors and DAL asset_statements preserved in Android resources

affects: [android-build-ci, device-verification]

tech-stack:
  added: ["@capacitor/core", "@capacitor/cli", "@capacitor/android", "typescript"]
  patterns: ["Capacitor server.url for server-rendered apps", "server.errorPath for offline fallback"]

key-files:
  created:
    - capacitor.config.ts
    - www/index.html
    - www/css/style.css
    - android/ (entire Capacitor-generated project)
  modified:
    - package.json
    - .gitignore
    - android/app/build.gradle (signing config added)
    - android/app/src/main/res/values/colors.xml (brand colors)
    - android/app/src/main/res/values/strings.xml (DAL asset_statements)
    - android/app/src/main/AndroidManifest.xml (asset_statements metadata)

key-decisions:
  - "Used Capacitor server.url (Option C) — loads from production backend, not bundled SPA"
  - "server.errorPath /index.html serves local offline fallback from www/"
  - "Kept same package ID app.dobryplan.twa for in-place APK updates"
  - "Added TypeScript as devDependency for Capacitor config parsing"

patterns-established:
  - "Capacitor webDir www/ contains offline fallback only, not full app"
  - "cap sync copies www/ to android/app/src/main/assets/public/"
  - "Signing config in android/app/build.gradle using env vars"

requirements-completed: [CAP-01, CAP-02, CAP-03, CAP-04]

duration: 8min
completed: 2026-03-30
---

# Plan 03-01: Initialize Capacitor Android Shell Summary

**Replaced TWA wrapper with Capacitor native Android shell — eliminates Chrome dependency, bundles offline fallback, retains same signing identity for in-place updates.**

## Performance

- **Duration:** 8 min
- **Tasks:** 2/2 complete
- **Files modified:** 10+

## Accomplishments
- Installed Capacitor core/CLI/Android packages with TypeScript config support
- Created capacitor.config.ts with production server.url, offline errorPath, and keystore config
- Built www/index.html offline fallback with brand styling (fully self-contained, no external deps)
- Replaced entire TWA android/ directory with Capacitor-generated project (BridgeActivity)
- Re-applied signing config (dobryplan-keystore.jks, same alias/package ID)
- Preserved brand colors, DAL asset_statements, and app icons in Android resources
- cap sync verified — web assets copied to android/app/src/main/assets/public/

## Task Commits

1. **Task 1: Install Capacitor and create project configuration** — `febcac0` (feat)
2. **Task 2: Replace TWA Android project with Capacitor Android shell** — `2127f8d` (feat)

## Files Created/Modified
- `capacitor.config.ts` — Capacitor config with appId, server.url, errorPath, keystore
- `www/index.html` — Offline fallback page with brand styling (self-contained)
- `www/css/style.css` — Tailwind CSS copied for potential initial load
- `android/app/build.gradle` — Capacitor build with release signing config
- `android/app/src/main/AndroidManifest.xml` — Capacitor MainActivity + DAL metadata
- `android/app/src/main/res/values/colors.xml` — Brand colors (primary, dark, accent)
- `android/app/src/main/res/values/strings.xml` — DAL asset_statements for URL verification
- `package.json` — Added @capacitor/core, @capacitor/cli, @capacitor/android, typescript
- `.gitignore` — Added android/app/build/, android/.gradle/, capacitor-cordova entries

## Self-Check: PASSED
- [x] capacitor.config.ts exists with correct appId and server.url
- [x] www/index.html exists with offline fallback
- [x] android/ is a Capacitor project (no LauncherActivity, no androidbrowserhelper)
- [x] Signing config uses dobryplan-keystore.jks
- [x] cap sync completed — assets in android/app/src/main/assets/public/
- [x] DAL asset_statements preserved in strings.xml
