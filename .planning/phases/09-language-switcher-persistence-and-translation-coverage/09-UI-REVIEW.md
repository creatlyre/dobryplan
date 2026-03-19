# UI Review — Phase 09: Language Switcher, Persistence & Translation Coverage

**Audit date:** 2026-03-19
**Phase scope:** Phases 8–9 (localization foundation + language switching)
**Locale tested:** Polish (pl) — default
**Overall score:** 13/24

---

## Pillar Scores

| Pillar | Score | Summary |
|--------|-------|---------|
| Copywriting | 1/4 | Zero diacritical marks in 137 Polish strings; hardcoded English in JS |
| Visuals | 3/4 | Consistent glassmorphism; event pill truncation aggressive |
| Color | 3/4 | Cohesive palette; today highlight clear; minor contrast concern on low-opacity text |
| Typography | 2/4 | Good hierarchy; Polish text at 10px too small for diacritics; no responsive adjustments for longer Polish strings |
| Spacing | 2/4 | Sidebar header overflows with Polish text; 3 items in single flex row |
| Experience Design | 2/4 | Mixed Polish/English UI; JS strings untranslated; functional but jarring |

---

## 1. Copywriting — 1/4

### CRITICAL: Polish diacritical marks completely missing

**0 out of 137 strings** in `app/locales/pl.json` contain any Polish diacritical characters (ą, ę, ś, ć, ź, ż, ó, ł, ń). Every string uses ASCII-only substitutes:

| Current (incorrect) | Correct Polish |
|---------------------|----------------|
| Ladowanie kalendarza | **Ł**adowanie kalendarza |
| Ladowanie wydarzen | **Ł**adowanie wydarze**ń** |
| Uzyj szybkiego dodawania | U**ż**yj szybkiego dodawania |
| formularz reczny | formularz r**ę**czny |
| Odswiez | Od**ś**wie**ż** |
| Zapros domownika | Zapro**ś** domownika |
| Zapros czlonka domownikow | Zapro**ś** cz**ł**onka domownik**ó**w |
| Blad OAuth callback | B**łą**d OAuth callback |
| Sprobuj ponownie | Spr**ó**buj ponownie |
| Nie mozna pobrac | Nie mo**ż**na pobra**ć** |
| Usun | Usu**ń** |
| Polacz Google | Po**łą**cz Google |
| Data rozpoczecia | Data rozpocz**ę**cia |
| Data zakonczenia | Data zako**ń**czenia |
| Wybierz rok | Wybierz rok *(ok)* |
| Zapisz wydarzenie | Zapisz wydarzenie *(ok)* |
| Wyloguj | Wyloguj *(ok)* |

This makes the app unacceptable for Polish users. Native speakers will perceive the text as broken or machine-generated.

**Fix:** Re-generate all 137 strings with proper Polish diacritics.

### Hardcoded English strings in JavaScript

The following strings in `app/templates/calendar.html` are hardcoded in English and never go through the `I18N` translation object:

| Line(s) | Hardcoded English | Should be |
|----------|-------------------|-----------|
| ~476 | `<strong>Members:</strong>` | `I18N.householdMembers` + pl key |
| ~510 | `Last successful sync: unknown` | needs I18N key |
| ~514 | `Last successful sync: ${formatSyncTimestamp(...)}` | needs I18N key with interpolation |
| ~517 | `Google OAuth is not configured on this server.` | needs I18N key |
| ~524 | `1 member` / `${n} members` | needs I18N key with pluralization |
| ~526 | `Google account not connected. Household: ...` | needs I18N key |
| ~534 | `Ready to sync. Household: ...` | needs I18N key |
| ~572 | `Synced ${n} event(s) across ${n} user(s).` | needs I18N key |
| ~603 | `Pull complete. No events found...` | needs I18N key |
| ~605 | `Pulled ${n} new event(s), updated ${n}...` | needs I18N key |
| ~609 | `Reconnect Google to grant calendar permissions.` | needs I18N key |

**Fix:** Add ~12 new I18N keys to both locale files and wire them into the JS `I18N` object.

---

## 2. Visuals — 3/4

### Good
- Glassmorphism design system is visually cohesive (glass panels, blur, borders)
- Calendar grid with rounded cells and subtle hover states works well
- Today's date highlight (indigo-500/30 + stronger border) is immediately visible
- Language switcher flag emoji approach (🇵🇱 / 🇬🇧) is clear
- Modals use consistent backdrop blur + centered panel pattern

### Issues
- **Event pills truncate aggressively** — At `text-[10px] sm:text-[11px]` in calendar cells, Polish event names like "Śmieci segregowane" or "Dzwonić absurdalnie" get cut to 5–6 characters: "09:00 Śmieci segr…". Little information is conveyed.
- **No tooltip on truncated event text** — Users cannot hover to see the full title in the calendar grid.

---

## 3. Color — 3/4

### Good
- Indigo/violet gradient background with glassmorphism creates a modern, unified feel
- Primary action buttons (glass-btn-primary) use a clear indigo→violet gradient
- Weekend column headers use `text-indigo-300/70` for subtle differentiation
- Error states use red-300/red-400 tones consistently
- Warning/ambiguity uses amber-300/amber-400 palette

### Minor
- Some helper text at `text-white/40` and `text-white/50` opacity could fail WCAG AA for small text sizes (contrast ratio < 4.5:1 against dark background). Not critical for decorative text but relevant for user-facing instructions.

---

## 4. Typography — 2/4

### Good
- Clear hierarchy: headings (`text-lg font-semibold`), body (`text-sm`), labels (`text-xs font-medium uppercase tracking-wide`)
- Calendar day numbers (`font-semibold`) are legible
- Weekday header abbreviations are appropriately short (PON, WT, ŚR, CZW, PT, SOB, NDZ — once diacritics are fixed)

### Issues
- **Calendar event pills at 10px are too small** — At `text-[10px]` (mobile) and `text-[11px]` (sm+), Polish characters with diacritics (ś, ź, ż, ó, ł) are harder to read than ASCII equivalents. Consider bumping to `text-[11px] sm:text-xs` (12px).
- **No responsive text adjustments for Polish** — Polish strings average ~30% longer than English. Sidebar section headings like "Wprowadzanie wydarzenia" and button labels like "Synchronizuj ten miesiąc" don't have breakpoint-aware sizing or wrapping strategies.
- **Sidebar button text** — "Szybkie dodawanie" (16 chars) vs "Quick Add" (9 chars) doesn't fit in the same button width without wrapping.

---

## 5. Spacing — 2/4

### Good
- Calendar grid uses `gap-1 sm:gap-2` which scales appropriately
- Sidebar cards have consistent `p-4` padding with `space-y-4` between them
- Modal panels use generous padding (`px-6 py-4`)

### Issues
- **Sidebar event entry header overflows** — The `flex items-center justify-between` row contains 3 items:
  1. `<h3>` "Wprowadzanie wydarzenia" (~22 chars)
  2. Button "+ Dodaj wydarzenie" (~18 chars)
  3. Button "⚡ Szybkie dodawanie" (~20 chars)

  In a ~280px sidebar column, these items cannot fit on one line. The "Szybkie dodawanie" button appears to break out of its container. In English ("Event Entry" + "+ Add Event" + "⚡ Quick Add") it barely fits.

  **Fix:** Stack the heading above the buttons, or use `flex-wrap` with a gap. Consider:
  ```html
  <div class="mb-3">
    <h3 class="text-lg font-semibold text-white mb-2">...</h3>
    <div class="flex flex-wrap gap-2">
      <button>...</button>
      <button>...</button>
    </div>
  </div>
  ```

- **Calendar cells `min-h-[84px]`** — Adequate for 2 English event pills, but Polish truncation means the cell height is wasted since the text is unreadable anyway.

---

## 6. Experience Design — 2/4

### Good
- Language switcher is accessible from nav bar on every page
- Cookie persistence works correctly (365-day httpOnly cookie)
- Locale resolution chain (query param → cookie → localStorage → Accept-Language → default) is solid
- Modal ESC/backdrop-click close patterns are consistent

### Issues
- **Mixed-language UI** — With Polish selected, the calendar shows:
  - Polish: navigation buttons, sidebar headings, form labels ✓
  - English: "Members: 1", "Ready to sync. Household: 1 member.", "Last successful sync: 19.03.2026, 16:16:30" ✗
  This creates a jarring bilingual experience.
- **Household section** — The `Members:` label and member count text are assembled in JavaScript without translation.
- **Sync result messages** — All sync success/failure/pull messages are English-only, even when the user has selected Polish.

---

## Top Fixes (Priority Order)

### 1. Add diacritical marks to all 137 Polish strings
**Impact:** Critical — the app is unusable for Polish readers without proper characters.
**Effort:** ~30 min — systematic find-replace across `app/locales/pl.json`.

### 2. Translate hardcoded JS strings
**Impact:** High — eliminates mixed-language experience.
**Effort:** ~45 min — add ~12 keys to both locale files, wire into JS `I18N` object.

### 3. Fix sidebar event entry header layout
**Impact:** Medium — currently overflows on Polish locale.
**Effort:** ~15 min — restructure the flex container to stack heading above buttons.

### 4. Add title tooltip to truncated calendar event pills
**Impact:** Low-medium — lets users see full event name on hover.
**Effort:** ~10 min — add `title="{{ event.title }}"` to the event pill `<div>` in `month_grid.html`.

### 5. Increase calendar event pill font size
**Impact:** Low — improves readability of Polish diacritics in calendar grid.
**Effort:** ~5 min — bump from `text-[10px] sm:text-[11px]` to `text-[11px] sm:text-xs`.
