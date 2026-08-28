<!-- bildfast:plan id=0006 status=approved agent=bildfast task="Enforce 'one use per customer' when a coupon is applied, not just at final invoice save" -->
# Plan: Enforce coupon "one use per customer" at apply-time

## Overview
User reported (in the coupon/offers management screen): "Maximum Usage" / usage-count and the
"allow one use per customer only" toggle look like they don't work.

Investigated both:
1. **Max usage / usage count** — direct downstream symptom of the bug fixed in plan 0005
   (`posa_coupon_code`): since every coupon checkout crashed before an invoice could ever reach
   "submitted", `POS Coupon.used` never incremented, so the limit could never be hit and the
   management screen's "Used: 0/N" never moved. No separate fix needed — already resolved by
   0005 going forward. Confirmed the `on_submit`/`on_cancel` hooks that increment/decrement
   `used` ARE registered in `hooks.py`'s `doc_events`, and `increment_coupon_usage()` itself has
   no bug — the only break was the field it read, fixed in 0005.
2. **"One use per customer" (`one_use`)** — a separate, real, still-open gap.
   `pos_next/api/offers.py`'s `validate_coupon()` (the check that runs the moment a cashier
   types/applies a coupon code in the cart) checks disabled/dates/min-max amount/global usage
   limit/customer-restriction — but never checked `one_use` at all. The only place that ever
   checked it was `check_coupon_code()` in `pos_coupon.py`, called from `update_invoice()` at
   final invoice save. Net effect: a coupon a customer already used could be "successfully"
   applied in the cart, then fail unpredictably at checkout.

While fixing #2, found a **regression risk in plan 0005's own fix**: the shared helper both
checks call, `_get_customer_coupon_usage_count()`, counts prior usage by filtering submitted
Sales Invoices on the **core `coupon_code` field** — the exact field plan 0005 stopped writing
to (moved to `posa_coupon_code`). Left as-is, the one-time-use check would always see 0 prior
uses and never actually block a repeat use, post-0005. Fixed in the same pass.

## Plan
- @bildfast (backend-only, 2 source files + 1 test file — done inline, no sub-agent; grepped
  the only call site of `validate_coupon` and all remaining `coupon_code` references first)
1. `pos_next/api/offers.py`: add the same one-time-per-customer check `check_coupon_code()`
   already does (via `_get_customer_coupon_usage_count`) to `validate_coupon()`.
2. `pos_next/pos_next/doctype/pos_coupon/pos_coupon.py`: `_get_customer_coupon_usage_count()`
   now filters on `posa_coupon_code` instead of the core `coupon_code` field.
3. `pos_next/pos_next/doctype/pos_coupon/test_pos_coupon.py`: updated the existing unit test's
   filter assertions to match.

## Execution Note
All three files verified with `python3 -m py_compile` (clean). Backend-only — no frontend
build needed.

Tried to actually run `test_pos_coupon.py` (both before and after my change, via
`bench --site pos.yemenfrappe.com execute` running unittest directly, since `bench run-tests`
is disabled on this site). Both the original **and** my updated version fail identically with
a `mock`/`frappe.db` coroutine-related error — confirmed via diffing against the original
committed file and re-running it unmodified. This is a **pre-existing environment issue**
(the mocks predate an async change in this bench's Frappe version) unrelated to my edit — my
change doesn't make it any more or less broken, and the assertions themselves are now correct
for the renamed field. Flagging rather than silently declaring "tests pass": the test
infrastructure for this file needs a separate look before it can be trusted in this
environment.

Committed separately from plan 0005 (different function/mechanism), per the one-fix-per-commit
rule.

**Update — resolved:** the `posa_coupon_code` column has since been created on this site (see
plan 0005's execution note — a single targeted `Custom Field` insert, not a full migrate), so
`_get_customer_coupon_usage_count()` now correctly sees real usage history here too. Both the
apply-time and save-time one-time-use checks are fully live on this site, not just in code.
