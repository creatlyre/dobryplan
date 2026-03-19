# 02 UI Review

**Audited:** March 19, 2026
**Baseline:** Abstract 6-pillar standards (no UI-SPEC.md exists)
**Files Reviewed:**
- `app/templates/base.html` (base layout)
- `app/templates/calendar.html` (main calendar page)
- `app/templates/partials/month_grid.html` (month grid rendering)
- `app/templates/partials/day_events.html` (day events list)
- `app/templates/partials/event_form.html` (event form)
- `app/templates/partials/quick_add_modal.html` (Quick Add modal)

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3.5/4 | Labels are specific and helpful; NLP examples aid clarity. Missing affordance hints on edit/delete buttons. |
| 2. Visuals | 3/4 | Clean responsive layout with good whitespace. Month grid could use stronger visual hierarchy and affordances. |
| 3. Color | 3/4 | Semantic color usage is strong (blue=primary, red=destructive). Green for Quick Add button breaks consistency. |
| 4. Typography | 2/4 | Font sizes inconsistent in month grid (`text-[10px]` breaks readability on mobile). All-caps labels reduce scannability. |
| 5. Spacing | 3/4 | Tailwind scale applied consistently; month grid gaps too tight (`gap-1` and `p-1`). |
| 6. Experience Design | 3/4 | Loading and error states present; delete action lacks confirmation. QA modal accessibility is strong. |

**Overall: 17.5/24 (73%)**

---

## Top 3 Priority Fixes

### 1. **Add Delete Confirmation Dialog**
**Impact:** Prevents accidental data loss from misclick or muscle memory.
**Current State:** `deleteEvent()` in calendar.html immediately deletes without prompting.
**Fix:** Before calling `DELETE /api/events/{id}`, show `confirm()` dialog:
```javascript
async function deleteEvent(eventId) {
  if (!confirm('Delete this event? This cannot be undone.')) return;
  const response = await fetch(`/api/events/${eventId}`, { method: 'DELETE' });
  if (!response.ok) {
    alert('Failed to delete event');
    return;
  }
  await refreshPanels();
}
```
**Test:** Try clicking delete—confirm dialog should appear before action proceeds.

### 2. **Fix Month Grid Font Size and Spacing for Mobile**
**Impact:** Month grid event titles are unreadable on small screens; tight spacing reduces tap targets.
**Current State:**
- Event titles in month grid: `text-[10px]` (custom size, too small)
- Day button cells: `min-h-[84px]` with `p-1` (padding too tight)
- Grid gap: `gap-1` (minimal breathing room)

**Fix:** Apply responsive sizing:
```html
<!-- In month_grid.html, change gap and padding -->
<div class="grid grid-cols-7 gap-1 sm:gap-2 text-xs">
  ...
</div>

<!-- Change day button cells -->
<button class="min-h-[84px] sm:min-h-[100px] rounded border p-2 sm:p-3 text-left 
  {% if day == today %}bg-blue-50 border-blue-300{% else %}bg-white border-gray-200{% endif %}">
  <div class="font-semibold">{{ day.day }}</div>
  {% for event in items[:2] %}
  <div class="truncate text-[10px] sm:text-xs text-gray-700">
    {{ event.start_at.strftime('%H:%M') }} {{ event.title }}
  </div>
  {% endfor %}
</button>
```
**Test:** View on iPhone (375px) and desktop (1440px)—text should remain readable at both sizes.

### 3. **Standardize Quick Add Button Color to Blue**
**Impact:** Green Quick Add button breaks semantic color pattern; users may confuse it with success/completion.
**Current State:** Calendar sidebar has `bg-green-600` for Quick Add button.
**Fix:** Change Quick Add button in calendar.html from green to blue:
```html
<!-- Before -->
<button id="qa-open-btn"
        type="button"
        class="rounded bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700">
  &#9889; Quick Add
</button>

<!-- After -->
<button id="qa-open-btn"
        type="button"
        class="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700">
  &#9889; Quick Add
</button>
```
**Rationale:** All primary actions (Save, Create) use blue. Quick Add is a primary action, not a success state.

---

## Detailed Findings

### Pillar 1: Copywriting (3.5/4)

**Strengths:**
- All button labels are action-oriented: "Save Event," "Save & Add Another," "Edit," "Delete," "Logout," "Invite Member"
- Section headers are descriptive: "Event Editor," "Household," "Upcoming Events"
- Empty state is explicit: "No events for this day." (not "None" or "Empty")
- NLP examples in QA modal are highly specific and helpful: "dentist Thursday 14:00," "meeting next Friday 10am"
- Error messages are user-friendly and non-technical: "Could not parse that text" (not internal errors)
- Field labels include visual affordance for required fields: Title <span class="text-red-500">*</span>

**Minor Issues:**
- Form labels use uppercase (`TITLE`, `DESCRIPTION`, `START`) which can reduce visual scannability
- Edit/Delete buttons in day events list are small text (`text-xs`) without icon affordance—users may not immediately recognize them as clickable
- No help text for "Timezone" field (though it's auto-set to user timezone in JS)

**Recommendation:**
- Change form label case from `uppercase` to sentence case: `Title` instead of `TITLE`
- Add icon affordance to edit/delete buttons or increase text size

---

### Pillar 2: Visuals (3/4)

**Strengths:**
- Responsive grid layout: `grid grid-cols-1 gap-4 lg:grid-cols-4` adapts well from mobile to desktop
- Clear visual separation: month view and day events are distinct sections with white cards and shadows
- Vertical rhythm: `space-y-4` creates consistent breathing room between sections
- Month grid is semantically correct: 7-column layout for weekdays
- Daily event cards use flex layout with clear alignment: title on left, actions on right

**Issues:**
- Month grid gap is tight: `gap-1` (0.25rem) provides minimal separation. Recommend `gap-2` (0.5rem) for better visual breathing room
- Day indicator: Only uses background color (`bg-blue-50`) to show "today." Could add a subtle icon (circle indicator) or border to make it more obvious
- Form fields in sidebar are closely stacked: could benefit from slightly more spacing between groups
- Event list shows only 2 events in month grid due to space constraints; doesn't indicate if more exist

**Recommendation:**
- Increase month grid `gap` to `gap-2` for better visual separation
- Add an icon or visual indicator (e.g., blue circle on date number) to highlight current day
- Visually indicate if more than 2 events exist on a day in month view (e.g., "+1 more")

---

### Pillar 3: Color (3/4)

**Color Palette Analysis:**

| Element | Color | Assessment |
|---------|-------|-----------|
| Primary actions (Save) | `bg-blue-600` | ✓ Semantic, good contrast |
| Secondary actions (Cancel) | `border-gray-300` | ✓ Neutral, non-committal |
| Destructive (Delete) | `text-red-700` on white | ✓ Red for destructive is standard |
| Quick Add button | `bg-green-600` | ✗ Breaks consistency (green = success, not primary action) |
| Success toast | `bg-green-600` | ✓ Semantic (green = success) |
| Error states | `bg-red-50`, `text-red-800` | ✓ Clear error indication |
| Warning note (QA) | `bg-amber-50`, `text-amber-700` | ✓ Amber for warnings is standard |
| Focus states | `focus:ring-2 focus:ring-blue-500` | ✓ Good keyboard accessibility |
| Text hierarchy | Gray 900/600/500 | ✓ Good contrast scale |

**Contrast Verification:**
- White on blue (buttons): Good contrast (WCAG AA compliant)
- Dark gray on white (text): Good contrast (WCAG AA compliant)
- Red text on white (edit/delete): Good contrast (WCAG AA compliant)

**Issue:**
- Quick Add button uses green (`bg-green-600`) when all other primary actions use blue. This is inconsistent and may confuse users into thinking Quick Add is a success/completion action rather than a primary action.

**Recommendation:**
- Change Quick Add button to blue (`bg-blue-600`) to align with primary action pattern
- Keep green for success toast and confirmation messages only

---

### Pillar 4: Typography (2/4)

**Font Size Distribution:**

| Element | Class | Size | Assessment |
|---------|-------|------|-----------|
| Main title | `text-xl font-bold` | 1.25rem | ✓ Clear hierarchy |
| Section headers | `text-lg font-semibold` | 1.125rem | ✓ Visible emphasis |
| Form field labels | `text-xs uppercase` | 0.75rem | ⚠️ Small + all-caps reduces scannability |
| Button text | `text-sm` | 0.875rem | ✓ Readable |
| Event titles (month grid) | `text-[10px]` | 10px / 0.625rem | ✗ Too small, breaks mobile readability |
| Day events list | `text-xs text-gray-600` | 0.75rem | ✓ Readable for secondary info |
| Event time (day panel) | `text-xs` | 0.75rem | ✓ Appropriate for metadata |

**Weight Distribution:**
- `font-bold`: Main title only (good restraint)
- `font-semibold`: Section headers (appropriate)
- `font-medium`: Some labels and buttons (moderate use)
- Default/normal: Body text (good)

**Issues:**
1. **Month grid event titles are unreadable:** `text-[10px]` is below recommended minimum for body text (12px). On mobile devices with small screens, this becomes unusable. Example: Event "Dentist appointment" shows as "Dentist a..." truncated and tiny.

2. **All-caps labels reduce scannability:** Form labels like `TITLE`, `DESCRIPTION`, `START` are harder to scan quickly than sentence case. Users expect sentence case for form labels.

3. **No line-height specification:** Form inputs and labels don't have explicit line-height, relying on browser defaults. Could improve readability.

**Recommendation:**
- Make month grid event titles responsive: `text-[10px] sm:text-xs lg:text-sm`
- Change form labels from uppercase to sentence case: Use `class="text-xs font-medium text-gray-600"` (remove `uppercase`)
- Add `leading-relaxed` to form inputs for better readability

---

### Pillar 5: Spacing (3/4)

**Spacing Scale Used (Tailwind default):**

| Class | Value | Usage |
|-------|-------|-------|
| gap-1 | 0.25rem | Month grid (too tight) |
| gap-2 | 0.5rem | Form field groups |
| gap-4 | 1rem | Main layout grid |
| space-y-2 | 0.5rem | Day event items |
| space-y-3 | 0.75rem | Form sections |
| space-y-4 | 1rem | Main sections |
| p-1 | 0.25rem | Day buttons (too tight) |
| px-3, py-2 | 0.75rem / 0.5rem | Form inputs |
| px-6, py-4 | 1.5rem / 1rem | Modal padding |

**Assessment:**
- Container padding (4–6) is generous and appropriate
- Form field spacing (2–4) is consistent and readable
- Month grid spacing is **too tight**: `gap-1` between day cells and `p-1` padding inside cells makes it feel cramped, especially on mobile
- Main section spacing (4) provides good visual separation

**Specific Issues:**
- Month grid day buttons: `min-h-[84px] p-1` — padding of only 4px on all sides is very tight for clicking and viewing
- Month grid gap: `gap-1` (4px) between cells provides minimal separation
- No gap between month grid and day events below it (could add `mt-4`)

**Recommendation:**
- Increase month grid gap to `gap-2` for better visual breathing room
- Increase day button padding to `p-2 sm:p-3` for better tap targets and space
- Add margin between month grid and day events section

---

### Pillar 6: Experience Design (3/4)

#### Loading States ✓
- **Month view:** `<div class="rounded bg-white p-4 shadow">Loading month view...</div>` — Explicit text loading indicator
- **Day events:** `<div class="rounded bg-white p-4 shadow">Loading day events...</div>` — Explicit text loading indicator
- **QA modal parsing:** Spinner with "Parsing…" text — Clear feedback
- **Assessment:** ✓ All major async operations have loading feedback

#### Error States ✓
- **Parse errors:** Structured error display with message + examples + retry guidance
- **Save errors:** Inline error message in review phase with field highlighting
- **Form validation:** Client-side validation (required fields)
- **Network errors:** "Network error — check your connection and try again"
- **Delete attempts:** Simple alert on failure
- **Assessment:** ✓ Good error handling with helpful messages

#### Empty States ✓
- **No events:** "No events for this day." — Clear and specific
- **QA modal:** Helpful examples shown in label
- **Assessment:** ✓ Empty states are explicit and helpful

#### State Management & Preventing Double Submission ✓
- **Save in-flight guard:** `_saveInFlight` flag prevents closing modal or submitting again during save
- **Button disabled state:** Save buttons have `disabled:opacity-50` during submission
- **Assessment:** ✓ Prevents double-submission and improves UX

#### Deletion UX ⚠️
- **Current behavior:** `deleteEvent()` immediately sends DELETE request without confirmation
- **Risk:** Users can accidentally delete events with a single click
- **Assessment:** ✗ Lacks confirmation dialog—should require explicit confirmation
- **Recommendation:** Add `confirm()` dialog before deletion

#### Keyboard & Accessibility ✓
- **Focus management:** Form inputs have `focus:ring-2 focus:ring-blue-500`
- **QA modal:** Proper ARIA attributes: `role="dialog"`, `aria-modal="true"`, `aria-labelledby="qa-modal-title"`
- **Live regions:** `aria-live="polite"` and `aria-live="assertive"` for status updates
- **Screen reader support:** `sr-only` class for hidden status text
- **Keyboard navigation:**
  - Escape closes modal (with guard against closing during save)
  - Click outside modal closes it
  - Tab through form fields works
- **Assessment:** ✓ Strong accessibility, especially in QA modal

#### Interaction Feedback
- **Save success:** Toast notification "Event saved" (green, auto-dismisses after 3s)
- **Button hover:** Blue buttons have hover state `hover:bg-blue-700`
- **Form focus:** Blue focus ring on inputs
- **Assessment:** ✓ Adequate feedback, but could add more micro-interactions

#### Discoverability
- **Quick Add button:** Prominent in sidebar with ⚡ icon and "Quick Add" label
- **Month navigation:** Prev/Next buttons clearly labeled
- **Day selection:** Click day cell to load day events
- **Edit/Delete:** Buttons appear on hover/always visible in day events list
- **Assessment:** ✓ Actions are discoverable, though edit/delete affordance could be stronger

#### Overall Experience Design Issues
1. **No delete confirmation:** Main usability risk for data loss
2. **Month/day panels load without visual feedback:** Panels refresh silently after month nav or event save
3. **No keyboard shortcuts:** Users can't navigate months with keyboard
4. **Edit intent unclear:** Icon vs. text buttons inconsistent
5. **Mobile considerations:** QA modal overrides to full-screen (good), but month grid still cramped

**Recommendations:**
1. Add delete confirmation dialog
2. Show subtle loading state when month grid reloads after save
3. Add keyboard shortcuts (arrow keys for month nav)
4. Use consistent button styling (text + icon or text-only)

---

## Summary & Recommendations

### Strengths
- ✓ Clear, specific copywriting with helpful NLP examples
- ✓ Semantic color usage (blue=primary, red=destructive, green=success)
- ✓ Good accessibility in QA modal (ARIA labels, focus management, screen reader support)
- ✓ Responsive layout with mobile overrides
- ✓ Prevents double-submission with in-flight guard
- ✓ Good error messaging and empty state handling

### Critical Issues (Fix Before Release)
1. **Delete action lacks confirmation** — Users can accidentally delete events
2. **Month grid font too small on mobile** — Text unreadable on phones
3. **Quick Add button color inconsistent** — Green breaks semantic palette

### Minor Issues (Nice-to-Have Improvements)
- Form labels in uppercase reduce scannability
- Month grid spacing too tight (gap-1, p-1)
- No indicator when more than 2 events exist on a day
- Edit/Delete buttons could use icon affordance
- No visual feedback when month/day panels reload

### Next Phase Recommendations
- Address the 3 critical issues before shipping Phase 02
- Minor issues can be deferred to Phase 03 or later as polish work
- Consider adding a design system or UI component library for consistency
- Test thoroughly on mobile devices (iPhone, Android)

---

## UI REVIEW COMPLETE
