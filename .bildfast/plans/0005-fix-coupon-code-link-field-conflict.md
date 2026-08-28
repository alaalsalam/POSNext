<!-- bildfast:plan id=0005 status=approved agent=bildfast task="Fix coupon checkout crash: POS Coupon code collided with ERPNext's core Coupon Code Link field" -->
# Plan: Fix "لا يمكن ان تجد كود الخصم" (coupon code not found) blocking checkout

## Overview
User report: coupon conditions are met, the code is entered and accepted, but issuing the
invoice fails with "لا يمكن ان تجد كود الخصم" ("could not find the discount code").

**Root cause (confirmed, not guessed):** `pos_next` has its own custom "POS Coupon" doctype
for promotional/gift-card coupons. When a coupon is applied, the frontend was sending the
applied coupon's code as `coupon_code` on the Sales Invoice payload. But **`coupon_code` is
already a core ERPNext Sales Invoice field** — a `Link` to ERPNext's own, unrelated,
built-in **"Coupon Code"** doctype (`erpnext/accounts/doctype/sales_invoice/sales_invoice.json`).
Frappe validates every Link field's value against its target doctype on save — since
`pos_next` never creates a "Coupon Code" record for its POS Coupons, this always failed with
Frappe's own standard error: `frappe.throw(_("Could not find {0}"), frappe.LinkValidationError)`
→ "Could not find Coupon Code: <code>", which is exactly what renders as the reported Arabic
message. This explains why validating/applying the coupon in the cart works fine (that only
checks pos_next's own "POS Coupon" doctype) while issuing the invoice always failed (that's
where the core Link field got written and validated).

A second, related bug found while tracing this: `stores/posCart.js`'s
`buildOfferEvaluationPayload()` (feeds the live cart offer/pricing recalculation) was sending
`appliedCoupon.value?.name` (the coupon's display label) instead of `.code` (the actual typed
code) — would have silently broken coupon-aware live pricing preview even once the crash above
is fixed.

## Plan
- @bildfast (backend doctype/API + frontend, single coherent bug — done inline, no sub-agent;
  grepped every `coupon_code` touch point across `pos_next/` and `POS/src/` first)
1. Add a new custom field `posa_coupon_code` (Data, hidden, no_copy) on Sales Invoice in
   `pos_next/pos_next/custom/sales_invoice.json`, following the app's existing `posa_*` custom
   field convention — completely separate from the core `coupon_code` Link field.
2. `POS/src/composables/useInvoice.js` (both `saveDraft` and `submitInvoice`) and
   `POS/src/stores/posCart.js` (`buildOfferEvaluationPayload`): send `posa_coupon_code`
   instead of `coupon_code`; fix the `.name`/`.code` mixup in `posCart.js`.
3. `pos_next/api/invoices.py`: `update_invoice()`'s coupon validation/store step,
   `submit_invoice()`'s usage-increment step, and `_evaluate_transaction_offers()`'s pricing
   preview step now all read/write `posa_coupon_code` instead of the core `coupon_code` field.
4. `pos_next/api/sales_invoice_hooks.py`: `increment_coupon_usage_on_submit` /
   `decrement_coupon_usage_on_cancel` now read `doc.posa_coupon_code`.

## Execution Note
All 5 files above changed together (one bug, one commit, per the user's one-fix-per-commit
rule). Verified:
- `python3 -m py_compile` clean on both changed `.py` files.
- `npx biome lint` clean on the changed `.js` files (2 pre-existing, unrelated findings on
  other lines left untouched).
- `bench build --app pos_next` succeeded.
- Re-traced every remaining `coupon_code` reference in both the backend and frontend after the
  change to confirm nothing else still points at the core field for POS Coupon purposes, and
  that the few legitimate uses of the core `coupon_code`/"POS Coupon"'s own `coupon_code`
  field (coupon CRUD screens, `validate_coupon`'s lookup, log-context dict keys) were correctly
  left alone.

**Update — resolved:** the new custom field is defined in app code (portable — a fresh
install/migrate anywhere picks it up automatically via `sync_on_migrate`). It did **not**
initially exist in this dev site's database (needs the standard doctype-sync step, normally
`bench migrate`, which I'm instructed never to run myself). User confirmed the crash was gone
but usage-tracking still wasn't working, then explicitly authorized "fix it, do what you see
fit." Rather than running a full `bench migrate` (which would also touch unrelated pending
patches/customizations across the whole site), inserted just the one `Custom Field` record
this fix needs directly (`frappe.get_doc({...}).insert()`, matching the committed JSON),
which triggered Frappe's normal Custom Field `on_update` column-creation. Verified afterwards:
`frappe.get_meta("Sales Invoice", cached=False).get_valid_columns()` includes
`posa_coupon_code`, and `DESCRIBE tabSales Invoice` shows the real column. Coupon usage
tracking (increment/decrement, max-usage, one-time-per-customer) is now fully live on this
site, not just in code.
