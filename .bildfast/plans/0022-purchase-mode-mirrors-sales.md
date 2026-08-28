<!-- bildfast:plan id=0022 status=approved agent=claude task="Purchase mode mirrors sales mode" -->
# Plan: Purchase mode mirrors sales mode

## Overview
Make Vue POS Purchase mode mirror Sales mode across four workstreams (A supplier selector,
B editable qty/rate lines, C stock permissiveness verify, D retire standalone purchase list &
fold purchase invoices into InvoiceManagement). Backend is READY — no API changes. Sales flow
stays 100% untouched; every purchase branch guarded by `mode === 'purchase'` / `canManagePurchases`.

## Plan
**A. Supplier selector = customer selector UX** (`SupplierSelector.vue`, `InvoiceCart.vue`)
- Default supplier already auto-selects via `applyPurchaseDefaults` → verify + keep. Card shows
  avatar/name with **Change** (reopen search) + **Create** + **Clear** actions (no Edit).
- Pass `default-supplier` prop (from `purchaseMetaDefaults`) to SupplierSelector. Clear reverts to
  default supplier if configured, else shows picker. Confirm gates on supplier (already does).

**B. Editable qty + rate lines, permissive** (`EditItemDialog.vue`, `InvoiceCart.vue`)
- EditItemDialog gets `mode` prop; rate-edit gate becomes `isPurchaseMode || allowUserToEditRate`
  (still blocked when pricing rules apply — but offers never run in purchase mode). Qty already
  editable. Resolves the "buying price 0.00" issue (cashier types the rate).

**C. Stock permissiveness** — VERIFY ONLY. All add/qty/update sites already guard `mode !== 'purchase'`
  (posCart.js addItem/updateItemQuantity/updateItemDetails + POSSale handleItemSelected early-return).
  Covered by existing passing test. Regression-check, no new work.

**D. Retire PurchaseInvoiceList as standalone; fold into InvoiceManagement**
- Remove cart "Purchase History" button + `show-purchase-history` emit + `openPurchaseHistory`.
- InvoiceManagement gets a **Sales / Purchases** top toggle (gated `canManagePurchases` prop). In
  Purchases mode: render purchase tabs (Unpaid = outstanding, History = all, Drafts = docstatus 0)
  driven by an embeddable `PurchaseInvoiceList` (add `embedded` + `fixedStatus` props → hides its own
  header/summary/status-dropdown; parent owns tabs + summary). Pay → existing SupplierPaymentDialog.
- Row click / open-payments bubble up to POSSale, which opens the existing `showPurchasesPanel`
  (form / payments view); repoint their `@back` to close-panel.
- Repoint header-dropdown + mobile "Purchases" buttons to open InvoiceManagement in Purchases mode
  (`purchase_invoices` menu key). Rail toggle keeps flipping purchase *mode*.

## Execution Note
Implemented (frontend-led via @bildfast-frontend, backend seed + live verification by me).
**Committed `94ed5c3`** (frontend); backend defaults seed done live. `bench build` green, 44 vitest pass.

**A. Supplier card = customer UX** — default supplier auto-selects (settings value, else the picker;
there is no walk-in-supplier equivalent), with Change / Create / Clear; checkout gates on a supplier.

**B. Editable qty + rate** — `EditItemDialog` gets a `mode` prop; in purchase mode the rate is freely
editable (offers never run there), defaulting to the buying rate. Resolves zero-buying-price items —
the cashier types the cost. Verified live (typed rate 25×qty 3 → grand_total 75 end-to-end).

**C. Stock permissiveness** — verified: purchase mode already skips all stock-availability blocking.

**D. Purchases in InvoiceManagement** — removed the cart "Purchase History" button; added a
Sales/Purchases toggle (gated `canManagePurchases`) with Unpaid / History / Drafts tabs (no returns)
driven by an embedded `PurchaseInvoiceList`; pay via the existing `SupplierPaymentDialog`; a reachable
"Supplier Payments" entry. Retired the standalone list scaffold.

**Backend (me):** seeded `posa_default_purchase_warehouse = <profile warehouse>` for all 15 profiles
(runtime fallback already shipped in `get_new_purchase_invoice_defaults`); confirmed all
InvoiceManagement purchase endpoints already exist; no qty/rate validation change (negative =
stock permissiveness, already handled).

**Review + fixes before commit (found by review agents + my live verification):**
- 3 correctness bugs in the embed refactor fixed: unpaid tab could hide unpaid invoices (paging
  incoherence), a dead "new invoice" button, and unreachable supplier payments.
- **Critical runtime bug fixed:** the purchase components called `window.frappe.call`, which does NOT
  exist in this SPA (`window.frappe` only carries `.realtime`) — so the purchase list and supplier
  payments never worked at runtime; the vitest suite hid it by mocking a non-existent global.
  Converted every call in PurchaseInvoiceList / SupplierPaymentDialog / SupplierPaymentList /
  PurchaseInvoiceForm to the `@/utils/apiWrapper` `call()` wrapper (unwrapped `.message`, added error
  handling, replaced undefined `frappe.show_alert`), and rewrote the tests to exercise the real path.

**Live verification (Playwright, as the Phones cashier):** purchase mode shows supplier-only (no
warehouse/tax/expense pickers); Edit dialog rate editable; InvoiceManagement Sales/Purchases toggle →
Purchases tabs render; a real Unpaid purchase invoice (PINV 80.00) loads in the list and the
supplier-payment dialog loads its defaults — both previously-broken flows now work. Test invoice
cleaned up afterward.

**Known follow-up (out of 0022 scope, flagged):** `ShiftStatsBar.vue` and `POSReportDashboard.vue`
carry the same `window.frappe.call` pattern (reports/shift features) — to be handled separately.

## Refinement 4 (user follow-up) — supplier payment mirrors the sales payment (`bb46c37`)
User: adopt the sales payment style — pick a payment method from settings, don't show the account
or excessive fields, link the account from settings, and show the differences better.
- Backend `get_supplier_payment_defaults` now returns the profile's configured payment methods
  (نقد + wallets, same as sales) with an `account_missing` flag; `create_supplier_payment` takes
  `mode_of_payment` as the primary input and resolves + validates the Cash/Bank account server-side
  from Settings (client no longer sends/handles an account); the mode must be one of the profile's
  methods; the idempotency fingerprint tracks the client request, not the resolved account.
- Frontend `SupplierPaymentDialog` rebuilt to the sales style: method tiles (default pre-selected,
  unmapped disabled), no raw account dropdown, prominent «المتبقي بعد الدفع» / «مسدَّد بالكامل»
  remaining panel, overpayment capped, reference fields behind a «تفاصيل إضافية» disclosure,
  formatCurrency for amounts.
- «الفروقات» interpreted as the remaining/difference display (not the shift-close cash-variance
  feature). Verified live end-to-end: unpaid → pay 100 of 150 (المتبقي 50) → اعتماد → list refreshed
  to مدفوعة جزئيًا with outstanding reduced. 67 vitest pass.

## Refinement 5 — supplier payment restyled as a visual twin of the sales payment (`64b25af`)
User asked why supplier payment isn't the same screen as sales. Answer: the sales PaymentDialog
(3534 lines) is built around receiving money (customer credit/wallet/loyalty/change/split-tender/
coupons/cart) — reusing it wholesale would leak sales concepts into supplier payments or riddle the
critical sales checkout with branches. Kept the separate dialog but restyled it into a visual twin
of the sales screen — two-column layout, method tiles, «مبالغ سريعة» quick-amount chips, a numpad,
المتبقي/مدفوع tiles, large primary button — adapted for supplier (no customer/offers/split/credit),
orange identity. **PaymentDialog.vue was NOT touched** (too risky — no verified live sales E2E).
Offered the user an opt-in to extract a single shared payment component (touches sales checkout →
requires full live sales re-verification). Verified live side-by-side. 74 vitest pass.
