<!-- bildfast:plan id=0007 status=approved agent=bildfast task="Show the logged-in cashier's name in the main POS header, shift open/close dialogs, and the daily (EOD) print report" -->
# Plan: Show cashier name across the POS UI + daily report

## Overview
User asked for the logged-in user's name to show in three places: the main POS interface,
the shift opening/closing dialogs, and the daily (EOD) closing report printout.

Checked each of the three before changing anything:
1. **Main POS header** — already shows the name via `UserMenu.vue` (always-visible next to the
   avatar), but the text label is `hidden` below the `sm:` breakpoint — left as-is (deliberate
   responsive pattern per `ui-system.md`; the avatar/initials still identify the user on narrow
   screens). No code change needed here.
2. **Shift opening/closing dialogs** — genuinely missing. Neither dialog showed who was
   opening/closing the shift.
3. **EOD print report** — the "POS Next EOD Report" Print Format already had a "الكاشير"
   (Cashier) line, but it rendered the raw login ID (e.g. `phones@gmail.com`) instead of the
   person's actual name.

## Plan
- @bildfast (small, additive, display-only — done inline, no sub-agent)
1. `POS/src/components/ShiftOpeningDialog.vue` / `ShiftClosingDialog.vue`: show the current
   user's display name (`useUserData()`, the same composable already used in the main header)
   near the top of each dialog.
2. `pos_next/pos_next/print_format/pos_next_eod_report/pos_next_eod_report.json`: the "الكاشير"
   line now renders `frappe.utils.get_fullname(doc.user)` instead of the raw `doc.user` login
   ID.

## Execution Note
- `ShiftOpeningDialog.vue`: added a "Cashier: {name}" line visible across all steps.
- `ShiftClosingDialog.vue`: added the same to the dark header strip, under the shift title.
- EOD print format: swapped `{{ doc.user or '' }}` for
  `{{ frappe.utils.get_fullname(doc.user) if doc.user else '' }}`.
- Verified `POS Closing Shift.user` is in fact populated correctly today (checked 5 real
  submitted records on this site) — the report just wasn't formatting it as a name.
- `npx biome lint` clean on both changed Vue files (2 pre-existing, unrelated findings left
  untouched). `bench build --app pos_next` succeeded.
- This print format is a doctype-export file (like the Workspace fixture from earlier), so — same
  as the coupon field — the committed JSON only takes effect on THIS dev site once synced.
  Pushed the updated `html` directly to the existing "POS Next EOD Report" Print Format record
  via a single `frappe.db.set_value(...)` (not a full migrate), matching the approach the user
  authorized earlier in this session. Verified by reading the value back from the DB.
