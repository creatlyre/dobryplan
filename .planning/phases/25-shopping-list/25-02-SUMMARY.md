---
phase: 25-shopping-list
plan: 02
status: complete
started: 2026-03-23
completed: 2026-03-23
---

# Plan 25-02 Summary: Frontend — Template, Navigation, i18n, Tests

## What was built

### View Route
- `app/shopping/views.py` — GET `/shopping` renders `shopping.html`

### Template
- `app/templates/shopping.html` — Full shopping list page with:
  - Add single item form with Enter key support
  - Section-grouped display with emoji headers and item counts
  - Uncategorized items section with "Pick section" button
  - Inline edit and delete for all items
  - Multi-add modal for pasting comma/newline-separated items
  - Section picker modal for learning keywords
  - Clear all button (with confirmation)
  - Loading skeleton and empty state
  - Toast notifications

### Navigation
- Desktop nav: Shopping link added in base.html (between Synco logo area and controls)
- Mobile bottom nav: Shopping bag icon added as 3rd item (before Settings)

### i18n
- 20+ bilingual keys added to `en.json` and `pl.json` under `shopping.*` namespace

### Tests
- `tests/test_shopping.py` — 20 tests:
  - ItemCRUD (5 tests): add, get grouped, update, delete, delete nonexistent
  - MultiAdd (3 tests): comma, newline, empty validation
  - AutoCategorize (2 tests): known item categorized, unknown uncategorized
  - KeywordLearning (1 test): learn and persist
  - Sections (3 tests): preset seeding, custom create, keywords endpoint
  - SharedAccess (1 test): items visible across household
  - ServiceUnit (4 tests): keywords loaded, normalize diacritics, parsing
  - ViewPage (1 test): page renders

### Infrastructure
- `tests/conftest.py` — Added `shopping_sections`, `shopping_items`, `shopping_keyword_overrides` tables to InMemoryStore

## Test Results
- 20/20 tests pass
- 313/314 total suite pass (1 pre-existing failure in calendar views)
