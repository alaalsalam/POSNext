<!-- bildfast:plan id=0015 status=approved agent=bildfast task="Standardize POS payment methods across all profiles: نقد default + 5 wallets, remove the rest" -->
# Plan: Standardize payment methods on every POS Profile

## Overview
User asked to make every POS Profile (all companies) use exactly this payment set, in this order,
with **نقد** as the default, and delete every other method (explicitly including مدى):
1. نقد (default)  2. محفظة جيب  3. محفظة حاسب  4. محفظة ون كاش  5. محفظة فلوسك  6. محفظه جولي

## Name mappings (surfaced for the user to correct if wrong)
The desired items map to these actual `Mode of Payment` record names:
- محفظة جيب → **جيب**, محفظة حاسب → **حاسب**, محفظة ون كاش → **ون كاش**,
  محفظة فلوسك → **فلوسك**, محفظه جولي → **جوالي** (Jawali), and مدى (to remove) → **مدي**.

## Investigation (before touching anything)
- 16 POS Profiles exist. `POS Payment Method` child table has only `mode_of_payment` /
  `default` / `allow_in_returns` (no per-row account) — accounts resolve via
  `Mode of Payment Account` / company defaults.
- ERPNext `POSProfile.validate_payment_methods()` **throws "Missing Account"** unless every mode
  in a profile has a `Mode of Payment Account` for that profile's company → checked coverage
  for all 6 target modes × every company first.
- **All 15 YER demo companies** have accounts for all 6 modes → clean save.
- **spare parts (محل الحصبة, SAR)** — a different, non-demo shop — has NO account for ون كاش /
  فلوسك / جوالي. Adding them there would fail validation.
- 1 open shift (Gold and Jewelry / gold@gmail.com) — confirmed safe: `make_closing_shift_from_opening`
  keeps unknown/removed modes with non-zero opening balances visible, so nothing is orphaned.
- Consulted the advisor before executing (money-adjacent bulk change); incorporated all its
  guidance below.

## Execution Note
- **Snapshotted** all 16 profiles' payment rows (incl. `allow_in_returns`, which the initial
  survey hadn't captured) to `/tmp/payments_snapshot.json` + printed to transcript before any
  mutation, as a rollback reference.
- Rewrote each profile's `payments` via `doc.save()` (full validation runs), per-profile
  try/except + commit so one failure can't abort the rest:
  - **15 YER profiles** → exactly [نقد, جيب, حاسب, ون كاش, فلوسك, جوالي], نقد `default=1`.
  - **spare parts** → [نقد, جيب, حاسب] (the 3 with accounts); the other 3 wallets excluded
    because they have no `Mode of Payment Account` for that SAR company. Reported, not silently
    dropped.
  - Preserved each existing mode's `allow_in_returns` value (did NOT blanket-set to 1 — that
    would newly permit wallet refunds nobody asked for); only the one genuinely new row (نقد on
    Super Market, which lacked it) got `allow_in_returns=1`.
  - Set `posa_cash_mode_of_payment = "نقد"` on all 16 (several previously defaulted to the now-
    removed English "Cash" mode; explicit beats fallback for cash/change reconciliation).
- **Result: 16/16 saved, 0 failures.** Verified: every profile has exactly the intended modes in
  the exact order (idx 1..6), نقد `default=1`, cash mode = نقد. `POS Settings.allowed_return_payment_modes`
  checked — all empty, no stale references to removed modes.
- **Verified end-to-end via the real frontend API**: `pos_next.api.bootstrap._get_payment_methods`
  (which the checkout Payment Dialog uses) explicitly `.orderby(idx)` and returns, for Phones:
  نقد(default) → جيب → حاسب → ون كاش → فلوسك → جوالي — the exact requested order.

## Deliberately NOT done (flagged to user)
- **Mode of Payment master records were NOT deleted or disabled** — "احذفها" was applied as
  remove-from-the-POS-profiles. The masters (مدي, Cash, الكاش, كريمي, محفظتي, موبايل موني, …) are
  linked from historical invoices; deleting breaks history. Offered `enabled=0` as an optional
  global follow-up — needs the user's OK first (it's site-wide).
- **spare parts' 3 missing wallets** — offered to create the SAR `Mode of Payment Account`s and
  add them if the user wants that shop fully included.
- This is site data (like the earlier role/warehouse/default-workspace changes), not shipped app
  code. Open POS sessions cache the old list until refresh / next shift open.
