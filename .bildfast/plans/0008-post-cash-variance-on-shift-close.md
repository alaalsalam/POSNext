<!-- bildfast:plan id=0008 status=approved agent=bildfast task="Optionally post cash shortage/surplus to accounts when closing a POS shift" -->
# Plan: Post cash shortage/surplus on shift close (optional, capped)

## Overview
New capability (not a bug fix) — confirmed with the user: when closing a shift, if a payment
method's counted cash differs from the expected amount, offer an **optional** button to post
that variance to accounting:
- **Shortage** (counted < expected) → debit the *cashier's own* designated account (money the
  cashier now owes the company for that payment mode).
- **Surplus** (counted > expected) → credit a *single, company-configured* surplus account.

Confirmed with the user (previous message):
1. Shortage account is **per cashier**, not shared.
2. Surplus account is **one account, configured once** per company/profile.
3. Posting is **optional** (a checkbox/button, not automatic) and only allowed **up to a
   configured cap** — past the cap, that payment mode's difference is left unposted for manual
   handling.
4. Granularity is **per payment method** (a shift can post a shortage on Cash and a surplus on
   Card in the same closing).

Investigated first (agent report): this is **greenfield** — `POS Closing Shift Detail` already
computes `difference` per payment method, but nothing in pos_next or core ERPNext ever posts it
to accounts. No existing "shortage account" / "surplus account" concept anywhere. HRMS (which
would have offered a ready-made "Employee Advance" ledger) is **not installed** on this site, and
there's no existing User↔Employee link in this app — so "the cashier's account" needs a plain
Account field per cashier, not an Employee-Advance-style mechanism.

## Design (proposed — flagging one open assumption below)
- **New field on `User`**: `posa_shortage_account` (Link → Account) — "POS Shortage Account".
  Set once per cashier via the standard User form (desk). Chosen over Employee because this app
  already identifies cashiers purely by User (`POS Closing Shift.user`), and Employee records
  don't exist for any cashier today — avoids inventing a new dependency.
- **New fields on `POS Settings`** (already the per-POS-Profile config doctype used for every
  other toggle in this app): `posa_surplus_account` (Link → Account) — "Surplus Account", and
  `posa_max_variance_for_posting` (Currency) — "Max Variance Allowed for Auto-Posting".
- **New field on `POS Closing Shift`**: `posa_variance_journal_entry` (Link → Journal Entry,
  read-only) so the closing shift shows what it posted, if anything.
- **Backend**: new whitelisted function (`pos_next/api/pos_closing.py` or alongside
  `pos_closing_shift.py`) that, given a submitted closing shift:
  - For each `payment_reconciliation` row with `abs(difference) > 0` and
    `abs(difference) <= posa_max_variance_for_posting`: resolves that mode of payment's GL
    account via the existing `get_payment_account()` helper (already used elsewhere in
    `invoices.py` — no new account-resolution logic needed), and adds a debit/credit pair to a
    **single Journal Entry for the whole shift**:
    - Shortage: Debit `User.posa_shortage_account`, Credit the payment mode's account.
    - Surplus: Debit the payment mode's account, Credit `POS Settings.posa_surplus_account`.
  - Rows over the cap are skipped and reported back to the frontend (not silently dropped).
  - If the cashier has no `posa_shortage_account` configured and there's a shortage to post,
    that row is skipped with a clear reason (not blocked/thrown) — same for a missing surplus
    account.
  - Submits the Journal Entry, links it back via `posa_variance_journal_entry`.
- **Frontend** (`ShiftClosingDialog.vue`): a checkbox "ترحيل فروقات النقد ضمن السقف المسموح"
  (Post cash variances within the allowed cap), shown only when at least one payment mode has a
  postable difference. After closing, calls the new API and shows which modes were posted vs.
  skipped (over cap / missing account) in the success view.

## Cap scope — corrected after user feedback
Initially assumed the cap applied per payment method; user corrected this after seeing the
plan: **one combined cap for the whole shift** — the SUM of the absolute difference across
every payment method is checked against `posa_max_variance_for_posting`. If the combined total
exceeds it, posting is unavailable for the *entire* shift (not just the excess rows) — this is
all-or-nothing, not a per-row filter. Updated the design and the field's description
accordingly before writing any code.

## business.md
User confirmed: skip documenting this in `business.md` for now.

## Execution Note
Implemented as designed, with one correction found through live testing (see below).

**Doctype/field changes:**
- `pos_next/pos_next/custom/user.json` (new file): `posa_shortage_account` (Link → Account) on
  core `User`, following the `custom/*.json` pattern already used for Sales Invoice.
- `pos_next/pos_next/doctype/pos_settings/pos_settings.json`: new collapsible "Cash Variance
  Posting" section — `posa_surplus_account` (Link → Account) and
  `posa_max_variance_for_posting` (Currency, combined-total cap, 0 = posting disabled).
- `pos_next/pos_next/doctype/pos_closing_shift/pos_closing_shift.json`: new
  `posa_variance_journal_entry` (Link → Journal Entry, read-only, no_copy).

**Backend:**
- `pos_next/pos_next/doctype/pos_closing_shift/pos_closing_shift.py`: `post_cash_variance()` —
  permission-checked (`frappe.has_permission(..., "submit", throw=True)`), rejects
  draft/already-posted shifts, computes the combined absolute variance, blocks entirely if over
  cap (or cap is 0), otherwise builds one Journal Entry with a debit/credit pair per payment
  method (shortage → cashier's account / payment account; surplus → payment account / surplus
  account), skipping (not throwing on) rows missing a configured account, and links the
  submitted entry back via `posa_variance_journal_entry`. Reuses `get_payment_account()` from
  `invoices.py` for GL account resolution — no new resolution logic. Errors during JE
  creation/submission are caught, logged via `frappe.log_error` (title first, context dict with
  `error` last, per house error-handling convention), and surfaced as a friendly error-ID
  message rather than a raw traceback.
- `pos_next/api/shifts.py`: `post_cash_variance()` — thin whitelisted wrapper, matching the
  existing `submit_closing_shift()` pattern in the same file.

**Frontend (`ShiftClosingDialog.vue` + `useShift.js`):**
- New `postCashVariance` resource (`useShift.js`), same style as `submitClosingShift`.
- A `combinedAbsoluteVariance` computed was added alongside the existing `getTotalDifference` —
  the existing one is a *net* total (a Cash shortage and a Card surplus can cancel out to 0),
  which would have hidden the opt-in checkbox exactly when there IS something postable. The new
  computed sums absolute per-row differences, matching the backend's cap check.
- Checkbox "Post cash variances within the allowed cap to accounting", shown only when
  `combinedAbsoluteVariance >= 0.005`, unchecked by default. On successful shift close, if
  checked, calls `postCashVariance` and shows the outcome (posted + JE name / over cap /
  no account configured / error) — posting failure never blocks or undoes the shift close
  itself, it's strictly best-effort after the fact.

**Testing:**
- 9 new unit tests in `test_pos_closing_shift.py` (mock-based, following this app's existing
  `test_reporting_access.py` style): shortage posting, surplus posting, combined-cap block,
  missing-account skip (not thrown), zero-cap disables posting, no-difference short-circuit,
  already-posted rejection, draft-shift rejection, permission-denied propagation. All 9 pass
  (verified by actually running them — `bench execute` + `unittest` runner, since
  `bench run-tests` is disabled on this site).
- New custom fields synced to this dev site's DB directly (not a full `bench migrate`, per the
  ongoing constraint): `frappe.reload_doc(...)` for the two first-party doctypes (POS Settings,
  POS Closing Shift — this is the correct, narrower Frappe API for resyncing one doctype's
  schema from its JSON file), and a direct `Custom Field` insert for `User` (core doctype, same
  approach as the earlier coupon-code fix). Verified all 4 new columns exist via
  `get_meta(..., cached=False).get_valid_columns()` and `DESCRIBE`.
- **Live, rolled-back dry run against real data** (`frappe.db.savepoint()` +
  `frappe.db.rollback()`, nothing persisted): used a real submitted Phones closing shift, real
  accounts (`Employee Advances - Ph` as a stand-in shortage account, `Sales - Ph` as a stand-in
  surplus account), forced a real -37.5 shortage on its Cash row via `frappe.db.set_value`
  (child-row-level, since Frappe correctly blocks `.save()`-level edits to a submitted parent),
  and called `post_cash_variance()` for real.
  - **First run failed** — caught a genuine bug: Journal Entry Account's `reference_type` is a
    restricted Select field (Sales Invoice / Purchase Invoice / Payment Entry / etc.); "POS
    Closing Shift" isn't a valid option, so setting it there threw
    `frappe.exceptions.ValidationError` inside real ERPNext validation. Fixed by dropping
    `reference_type`/`reference_name` from the JE account rows — traceability instead comes
    from `posa_variance_journal_entry` on the closing shift and the entry's own `user_remark`.
  - **Second run succeeded**: created and submitted a real Journal Entry
    (`ACC-JV-2026-00009` in the test run) — `Employee Advances - Ph` debited 37.5,
    `POS Demo Ph Cash - Ph` credited 37.5. Confirmed the rollback left zero residue afterward
    (`frappe.db.exists` for that JE and the closing shift's `posa_variance_journal_entry`
    both came back empty).
- `python3 -m py_compile` clean on all changed `.py` files; `npx biome lint` clean on the
  changed `.vue`/`.js` files; `bench build --app pos_next` succeeded.

Committed as `feat: optionally post cash shortage/surplus to accounting on shift close`
(commit `bcb047e`).
