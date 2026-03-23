---
phase: 25-shopping-list
plan: 01
status: complete
started: 2026-03-23
completed: 2026-03-23
---

# Plan 25-01 Summary: Backend — DB, Models, Keywords, Repository, Service, API

## What was built

### Database Migration
- `supabase/migrations/20260323_shopping_list.sql` — 3 tables: `shopping_sections`, `shopping_items`, `shopping_keyword_overrides`

### Models
- `ShoppingSection`, `ShoppingItem`, `ShoppingKeywordOverride` dataclasses in `app/database/models.py`

### Keywords
- `app/shopping/keywords.json` — 150+ Polish grocery keywords across 10 Biedronka store sections

### Schemas
- `app/shopping/schemas.py` — `ShoppingItemCreate`, `ShoppingItemUpdate`, `MultiItemCreate`, `ShoppingSectionCreate`, `ShoppingSectionUpdate`, `KeywordLearn`

### Repository
- `app/shopping/repository.py` — `ShoppingRepository` with full CRUD for items, sections, keyword overrides. Preset section seeding for Biedronka layout.

### Service
- `app/shopping/service.py` — `ShoppingService` with auto-categorize (keyword JSON + user overrides), multi-item parse (comma/newline), keyword learning via upsert

### API Routes
- `app/shopping/routes.py` — 11 REST endpoints at `/api/shopping/*`:
  - Items: GET, POST, POST multi, PUT, DELETE, POST learn
  - Sections: GET, POST, PUT, DELETE
  - Keywords: GET

### main.py
- Shopping API router registered

## Decisions
- Sort orders start from 1 (to avoid `0` falsy issues in test store sorting)
- Auto-categorization: user overrides checked first, then built-in keywords
- Upsert implemented as select-then-insert/update (SupabaseStore lacks native upsert)
