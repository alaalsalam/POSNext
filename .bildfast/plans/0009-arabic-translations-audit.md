<!-- bildfast:plan id=0009 status=approved agent=bildfast task="Add missing Arabic translations for untranslated UI strings" -->
# Plan: Translate untranslated messages to Arabic

## Overview
User asked for the displayed messages to be translated to Arabic. Audited every `__()`-wrapped
string across `POS/src` (1119 unique strings) against `pos_next/translations/ar.csv` (the app's
Arabic translation file) rather than guessing which ones — found 215 with no Arabic entry.

Of those, 99 were false positives: some screens (purchase invoices, supplier payments, the
login page) call `__()` with an **already-Arabic** source string, so they render correctly
today with no CSV row needed. The remaining **116 were genuinely untranslated English** —
mostly recent additions from this session (shift closing, cash variance posting, cashier name
display) but also a good number of pre-existing strings (branding settings, offline-mode
banners, purchase invoice fields, catalog management) that predate this session entirely.

## Plan
- @bildfast (translation-data-only, no logic change — done inline, no sub-agent)
- Translate all 116 strings into Arabic matching this file's existing terminology/register
  (checked conventions first: e.g. "Difference" → "العجز / الزيادة", "Cash Short"/"Cash Over" →
  "نقص نقدي"/"زيادة نقدية", duration abbreviations "{0}h {1}m" → "{0}س {1}د"), append to
  `pos_next/translations/ar.csv`.

## Execution Note
Added 115 rows (skipped the one bare `"..."` string — nothing to translate). Verified:
- `csv` module re-parse of the whole file after the append — still valid, no malformed rows
  introduced (file has some pre-existing 2-column rows from before this change; unrelated).
- This app's translations load live via `pos_next.api.localization.get_app_translations` →
  Frappe's `frappe.translate.get_all_translations(lang)`, which is Redis-cached
  (`merged_translations` key) — NOT tied to the frontend build. Cleared that cache key on the
  site and spot-checked 8 of the new entries (including ones spanning shift closing, cash
  variance posting, and a purchases string) via
  `frappe.translate.get_all_translations("ar")` — all resolved to the correct new Arabic text.
  No `bench build` needed for this change.

Committed as `i18n: add Arabic translations for 115 untranslated strings across the app`
(commit `a1dccbd`).

Scope note: this covers every string currently reachable via a plain `__("...")` call in
`POS/src`. It does not cover: (a) doctype/field labels shown only in Desk admin forms (e.g. the
new `POS Shortage Account` field on User) — those are a different, lower-priority surface since
cashiers don't see them; (b) any dynamically-built strings that aren't literal `__("...")` calls
at the source level (a targeted grep can't see those) — flagging so it isn't presented as
"100% of all text," if you spot one, tell me the exact string and I'll add it.
