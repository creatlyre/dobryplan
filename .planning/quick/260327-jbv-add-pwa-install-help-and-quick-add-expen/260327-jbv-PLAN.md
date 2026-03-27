---
phase: 260327-jbv
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - public/manifest.json
  - app/budget/expense_views.py
  - app/budget/expense_service.py
  - app/templates/base.html
  - app/templates/partials/pwa_help_modal.html
  - app/locales/en.json
  - app/locales/pl.json
autonomous: true
requirements: [PWA-HELP, PWA-SHORTCUT, AUTO-CAT]

must_haves:
  truths:
    - "Footer shows a '?' help button alongside Terms · Privacy · Refund"
    - "Clicking '?' opens a modal with PWA install instructions for Chrome and Firefox on Android"
    - "Long-pressing the app icon on Android Chrome shows a 'Quick Add Expense' shortcut"
    - "The shortcut deep-links to /budget/quick-expense which opens the expense page with the quick-add modal auto-opened"
    - "Creating an expense without a category auto-detects category via keyword matching"
  artifacts:
    - path: "public/manifest.json"
      provides: "shortcuts array with Quick Add Expense entry"
      contains: "shortcuts"
    - path: "app/templates/partials/pwa_help_modal.html"
      provides: "PWA install help modal with Chrome + Firefox instructions"
    - path: "app/budget/expense_views.py"
      provides: "/budget/quick-expense route"
      exports: ["quick_expense_page"]
    - path: "app/budget/expense_service.py"
      provides: "Auto-categorization on create_expense"
  key_links:
    - from: "public/manifest.json"
      to: "/budget/quick-expense"
      via: "shortcuts[0].url"
      pattern: "quick-expense"
    - from: "app/templates/base.html"
      to: "app/templates/partials/pwa_help_modal.html"
      via: "include directive"
      pattern: "pwa_help_modal"
    - from: "app/budget/expense_views.py"
      to: "budget_expenses.html"
      via: "TemplateResponse with auto_open_quick_expense=True"
      pattern: "auto_open_quick_expense"
    - from: "app/budget/expense_service.py"
      to: "_detect_category"
      via: "called in create_expense when no category_id"
      pattern: "_detect_category"
---

<objective>
Add a "?" PWA install help button in the footer, a manifest shortcut for quick-adding expenses from the Android home screen, and auto-categorize expenses on creation.

Purpose: Users need clear instructions on how to install the PWA, and power users want a fast shortcut to log expenses without opening the full app.
Output: Help modal, manifest shortcut, /budget/quick-expense deep-link route, auto-categorization on create.
</objective>

<execution_context>
@~/.copilot/get-shit-done/workflows/execute-plan.md
@~/.copilot/get-shit-done/templates/summary.md
</execution_context>

<context>
@public/manifest.json
@app/budget/expense_views.py
@app/budget/expense_service.py
@app/templates/base.html (footer section, lines 149-158; modal includes, lines 231-232)
@app/templates/partials/quick_add_expense_modal.html
@app/locales/en.json
@app/locales/pl.json
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add PWA help modal and footer button + manifest shortcut</name>
  <files>
    app/templates/partials/pwa_help_modal.html,
    app/templates/base.html,
    public/manifest.json,
    app/locales/en.json,
    app/locales/pl.json
  </files>
  <action>
1. **Create `app/templates/partials/pwa_help_modal.html`** — a dialog modal with:
   - `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to heading
   - Close button with min 44px touch target
   - Two sections: Chrome Android instructions and Firefox Android instructions
   - Chrome: Menu (⋮) → "Install app" / "Add to Home Screen" → Confirm
   - Firefox: Menu (⋮) → "Install" / "Add to Home Screen" → Confirm
   - Note about long-press on app icon for Quick Add shortcut (Chrome only)
   - All text via i18n keys (`pwa_help.*`)
   - Escape key closes modal, focus trap inside modal
   - Glass styling matching existing modals (see `qa-expense-modal` for reference)

2. **Update `app/templates/base.html`** footer section:
   - After the Refund link (line ~156), add `<span>·</span>` and a `<button>` with `id="pwa-help-btn"`, text "?", `aria-label="{{ t('pwa_help.trigger_label') }}"`, same hover classes as existing links
   - Include the new partial after the existing quick_add_expense_modal include (line ~232): `{% include "partials/pwa_help_modal.html" %}`
   - Add inline JS at the bottom (or in existing script block) to wire button click → show modal, close button → hide modal, Escape → hide, backdrop click → hide

3. **Update `public/manifest.json`** — add `shortcuts` array:
   ```json
   "shortcuts": [
     {
       "name": "Quick Add Expense",
       "short_name": "Expense",
       "description": "Quickly add a one-time expense",
       "url": "/budget/quick-expense",
       "icons": [{ "src": "/static/icons/icon-192.png", "sizes": "192x192" }]
     }
   ]
   ```

4. **Add i18n keys to `en.json` and `pl.json`**:
   - `pwa_help.trigger_label`: "How to install this app" / "Jak zainstalować tę aplikację"
   - `pwa_help.title`: "Install Dobry Plan on your phone" / "Zainstaluj Dobry Plan na telefonie"
   - `pwa_help.chrome_title`: "Chrome (Android)" / "Chrome (Android)"
   - `pwa_help.chrome_step1` through `chrome_step4`: step-by-step Chrome install instructions
   - `pwa_help.firefox_title`: "Firefox (Android)" / "Firefox (Android)"
   - `pwa_help.firefox_step1` through `firefox_step3`: step-by-step Firefox install instructions
   - `pwa_help.shortcut_tip`: "Tip: Long-press the app icon for Quick Add Expense (Chrome only)" / Polish equivalent
   - `pwa_help.close`: "Close" / "Zamknij"
  </action>
  <verify>
    <automated>python -c "import json; m=json.load(open('public/manifest.json')); assert 'shortcuts' in m; assert m['shortcuts'][0]['url']=='/budget/quick-expense'; en=json.load(open('app/locales/en.json')); assert 'pwa_help.title' in en; pl=json.load(open('app/locales/pl.json')); assert 'pwa_help.title' in pl; print('PASS')"</automated>
  </verify>
  <done>Footer has "?" button, clicking it shows PWA install help modal with Chrome+Firefox steps. Manifest has shortcuts array pointing to /budget/quick-expense. i18n keys in both en.json and pl.json.</done>
</task>

<task type="auto">
  <name>Task 2: Quick-expense deep-link route + auto-categorize on create</name>
  <files>
    app/budget/expense_views.py,
    app/budget/expense_service.py,
    app/templates/budget_expenses.html
  </files>
  <action>
1. **Add `/budget/quick-expense` route in `expense_views.py`**:
   - New GET endpoint `quick_expense_page` — same pattern as `expenses_page` but adds `auto_open_quick_expense=True` to the template context
   - Renders the same `budget_expenses.html` template
   - Reuses same dependencies: `get_current_user`, `get_db`, `get_user_plan_for_template`

   ```python
   @router.get("/quick-expense", response_class=HTMLResponse)
   async def quick_expense_page(
       request: Request,
       user=Depends(get_current_user),
       db=Depends(get_db),
   ):
       context = inject_template_i18n(
           request,
           {
               "request": request,
               "user": user,
               "user_plan": get_user_plan_for_template(user, db),
               "auto_open_quick_expense": True,
           },
       )
       response = templates.TemplateResponse(request=request, name="budget_expenses.html", context=context)
       set_locale_cookie_if_param(response, request)
       return response
   ```

2. **Add auto-open JS in `budget_expenses.html`**:
   - At the end of the script block, check for `auto_open_quick_expense` context variable
   - If true, after DOMContentLoaded, trigger the same logic that opens the `#qa-expense-modal` (set `display: flex`, focus first input)
   - Pattern: `{% if auto_open_quick_expense %}document.addEventListener('DOMContentLoaded', () => { /* open qa-expense-modal */ });{% endif %}`

3. **Wire auto-categorization in `expense_service.py`**:
   - In `create_expense`, if `payload.category_id` is None (or falsy), call `self.list_categories(calendar_id)` then `self._detect_category(payload.name, categories)`. If a match is found, set `payload.category_id = detected` before passing to repo.
   - Same logic in `bulk_create`: for each item without `category_id`, detect and assign.
   - This is ~5 lines of code in each method.
  </action>
  <verify>
    <automated>python -c "from app.budget.expense_views import router; routes=[r.path for r in router.routes]; assert '/quick-expense' in routes; print('Route OK'); from app.budget.expense_service import ExpenseService; import inspect; src=inspect.getsource(ExpenseService.create_expense); assert '_detect_category' in src; print('Auto-cat OK')"</automated>
  </verify>
  <done>/budget/quick-expense route exists and renders expense page with modal auto-opened. create_expense and bulk_create auto-detect category when none provided.</done>
</task>

</tasks>

<verification>
- `python -m pytest tests/test_expenses.py -x` — existing expense tests still pass
- Visit `/budget/quick-expense` — expense page loads with quick-add modal pre-opened
- Footer "?" button opens PWA help modal with install instructions
- `manifest.json` validates with shortcuts array
- Creating an expense named "Biedronka" without a category auto-assigns "Groceries"
</verification>

<success_criteria>
1. Footer displays "?" button that opens a bilingual PWA install help modal
2. manifest.json has shortcuts pointing to /budget/quick-expense
3. /budget/quick-expense route exists and auto-opens the quick-add expense modal
4. Expenses created without a category are auto-categorized via keyword matching
5. All existing tests pass
</success_criteria>

<output>
After completion, create `.planning/quick/260327-jbv-add-pwa-install-help-and-quick-add-expen/260327-jbv-SUMMARY.md`
</output>
