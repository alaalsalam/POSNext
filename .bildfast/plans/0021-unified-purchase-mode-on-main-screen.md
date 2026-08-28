<!-- bildfast:plan id=0021 status=approved agent=bildfast task="Add a Purchase mode to the main POS screen (toggle party customer↔supplier), reusing the sales design, instead of a separate purchase form" -->
# Plan: Purchase Invoices on the main POS screen (mode toggle), same design

## Overview
User: adding a Sales Invoice uses the main screen (product grid + cart), and there's an
"Order" (طلب) toggle that makes it a Sales Order instead. He wants **Purchase Invoices to work
the same way** — a button/mode on the **same main screen** that flips the party field from
**Customer → Supplier** and builds a purchase instead of a sale. "نحافظ على التصميم" — keep the
design; don't send the user to a separate form.

## Why this fits the existing design (confirmed in code)
- The main cart already toggles `cartStore.targetDoctype` between **Sales Invoice** and **Sales
  Order** (`InvoiceCart.vue` → `selectDocType(...)`), reusing the same grid/cart. Adding a
  **Purchase Invoice** mode is the same pattern, one more option.
- The **purchase backend already exists** (`pos_next/api/purchases.py`): `get_suppliers`,
  `get_purchase_items`, `get_item_buying_price`, `save_purchase_invoice`,
  `submit_purchase_invoice`, `get_purchase_tax_templates`, `get_warehouses`,
  `get_expense_accounts`, supplier-payment flow. So this is mostly a **frontend unification**,
  not new backend.

## What "Purchase mode" changes on the same screen (design decisions — please confirm)
It's not only a label swap; sales and purchase differ in real ways. Proposed behavior:
1. **Party field:** Customer selector → Supplier selector (`get_suppliers` / `create_supplier`).
2. **Prices:** items show **buying price** (`get_item_buying_price`), not the selling price.
3. **Checkout:** builds a **Purchase Invoice** (`save_/submit_purchase_invoice`) with
   `update_stock` so stock goes **in**; a purchase tax template instead of sales tax.
4. **Payment:** money is **paid out to the supplier** (not received) — reuse the supplier-payment
   flow, or leave the invoice unpaid for later payment. → **Decision needed:** pay-at-checkout,
   or create-invoice-then-pay-later?
5. **Hidden in purchase mode** (sales-only concepts): offers/coupons, loyalty/wallet, customer
   credit, returns, Sales Order toggle, delivery date.
6. **Extra purchase fields:** target warehouse + (for expense items) expense account — surfaced
   compactly so the screen still feels like the POS, not a full ERP form.

## Proposed approach (phased, on approval)
- **Frontend (@bildfast-frontend, the bulk):** add a top-level **Sales / Purchase** mode switch
  on the main screen; drive it off a `cartStore.mode` (or extend `targetDoctype` with
  "Purchase Invoice"); make the party selector, price source, cart totals, and the checkout
  button reactive to the mode; hide sales-only widgets in purchase mode. Reuse the existing
  product grid + cart components as-is.
- **Backend (@bildfast-backend, small):** the APIs exist; add only thin glue if the unified
  checkout needs it (e.g. a single "build purchase from cart" shape matching the cart payload),
  each with its access check. Gated by the existing `enable_purchases` feature flag + POS
  Manager (so cashiers don't get purchase mode unless allowed) — reusing the current permission
  model, not widening it.
- **Migration:** keep the current separate Purchases panel working during rollout; once the
  in-screen mode is proven, the old panel can be retired (or kept as the "purchase history/list"
  view, which the main screen doesn't cover).
- **Tests:** API tests already exist for purchases; add cart-mode unit tests (mode switch resets
  party/price correctly; checkout routes to the right doctype) + a purchase-mode happy-path.

## Open decisions for you
1. **Payment:** pay the supplier at checkout, or save the purchase invoice and pay later from the
   existing supplier-payments screen?
2. **Who gets purchase mode:** managers only (current `enable_purchases` + POS Manager), or any
   cashier when the flag is on?
3. **The list/history:** keep a "purchase invoices list" somewhere (the main screen is for
   creating one at a time) — reuse the current `PurchaseInvoiceList` as a history tab?

## Decisions taken (user approved "implement now" without picking)
1. Payment: create+submit the Purchase Invoice at checkout, then a **skippable** supplier payment
   (close = save unpaid, pay later). 2. Gating: managers only (`enable_purchases` + POS Manager).
   3. History: existing `PurchaseInvoiceList` reachable as "Purchase History".

## Execution Note
Implemented (frontend-led via @bildfast-frontend, backend glue + fixes by me), applied live,
verified in the browser.

**Frontend** (`stores/posCart.js` + `.test.js`, `components/purchases/SupplierSelector.vue` [new],
`components/sale/InvoiceCart.vue`, `components/sale/ItemsSelector.vue`, `pages/POSSale.vue`):
Sales/Purchase mode toggle on the main screen (gated by `canManagePurchases`); supplier selector
replaces the customer selector (stored separately from `customer` so the offers watcher /
cart-recovery snapshot never treat a supplier as a customer); grid + added items show buying
prices (orange); compact warehouse + tax-template + expense-account row; "Confirm Purchase"
checkout → `save_`+`submit_purchase_invoice` (update_stock) → skippable `SupplierPaymentDialog`;
sales-only widgets hidden in purchase mode. **Sales flow untouched** — every purchase branch
guarded by `mode === 'purchase'`, and all four stock-validation sites + offers + cart-recovery
skip purchase mode. Purchase checkout blocked offline. **22 frontend tests pass** (8 new cart-mode).

**Backend** (`api/purchases.py`): one new `get_buying_prices` (bulk map, no N+1; guarded by
purchases-feature + manager role + Item Price read + validated buying price list). Security-
reviewed: `require_manager_feature` enforces flag + manager + Company read; no injection.

**Fixed a real blocker found during live test:** switching to purchase mode 417'd because this
site's `Buying Settings.buying_price_list` pointed at a **selling** list ("البيع القياسية"); the
code correctly rejected it. Corrected the site setting to the real enabled buying list
("شراء القياسية") **and** hardened `_default_buying_price_list` to fall back to a valid enabled
buying list when the configured one is unset/wrong (so fresh installs / misconfigured sites don't
hard-fail). After the fix, purchase mode activates cleanly — verified live: toggle → supplier
field + buying-price grid + Confirm Purchase render; sales mode still intact.

**Known data caveats (not code bugs — flagged to user):**
- Buying prices show **0.00** for Phones items because no buying prices are entered in the buying
  price list yet (data entry).
- ~~**Warehouse dropdown is empty for Phones**: Phones' user is permission-restricted to
  `Phones - Ph`, which is a **group** warehouse …~~ **CORRECTED (this was wrong on both counts).**
  `Phones - Ph` is a **non-group leaf** the user is permitted to, and the empty dropdown was **not**
  Phones-specific — it hit **every** restricted cashier (all 14 companies). Real root cause: a
  systemic backend bug. With `apply_strict_user_permissions=1`, the per-profile Warehouse User
  Permission cascaded onto Warehouse's own self-referential Link `default_in_transit_warehouse`
  (empty on nearly every row), so strict mode excluded **all** warehouses from `get_warehouses`
  (proven via the extracted SQL match-condition). **Fixed** by shipping a Property Setter marking
  that link `ignore_user_permissions` (mirrors how core already treats `parent_warehouse`):
  `patches/v2_0_0/warehouse_transit_ignore_user_perms.py` (+ registered in patches.txt), applied
  live. After the fix `get_warehouses` returns exactly the user's permitted warehouse
  (`phones→Phones - Ph`, `chocolates→Finished Goods - Ch`) — restriction preserved, no longer empty.
  Regression test: `tests/test_warehouse_user_permission.py`.
- Deferred (per the frontend agent, to preserve "reuse the same grid"): the grid still uses the
  **sales** item cache, so sales-only items appear (would be rejected at purchase checkout by the
  backend's "not enabled for purchasing") and purchase-only items outside the POS catalog aren't
  findable from the grid.

Committed as `c1e4c10`. `bench build` succeeded.

## Docs
Per the ownership rule I did not edit `business.md` / `tests.md`. This IS a new capability, so
I'll propose a "Purchases (in-POS)" business entry + a purchase-mode test scenario for you to
approve — see the reply.

## Status
`approved` — implemented, applied live, verified. See Execution Note.

## Refinement (user follow-up, approved & done)
User: the Purchase toggle's placement was unsuitable — move it to the side rail as a mode
activation; and add purchase defaults in Settings like the sales default customer.
- **Toggle moved to the side rail** (`ManagementSlider.vue`): the "Purchases" icon now toggles
  purchase mode with an active orange highlight (title flips "Activate/Exit purchase mode"); the
  cart-header segmented toggle was removed (shows a "Purchase Mode" label); confirm-before-wipe
  moved to `POSSale`; the in-cart "Purchase History" button opens the list, decoupled from the
  toggle.
- **Purchase Defaults in POS Settings** — new fields `posa_default_supplier` /
  `posa_default_purchase_warehouse` / `posa_default_purchase_tax_template` /
  `posa_default_expense_account` (synced live); `get_new_purchase_invoice_defaults` returns them
  (+ supplier display name); a "Purchase Defaults" settings section configures them and purchase
  mode pre-fills them when empty. Sales default customer stays on the POS Profile as-is; these
  purchase defaults live on POS Settings (the pos_next-owned per-profile config).
- Backend by me (`dcb8478` + supplier-name add), frontend by @bildfast-frontend. Verified live
  (rail toggle activates+highlights; sales mode restores cleanly), 24/24 tests, build green.
  Commits `dcb8478`, `0397759`.

## Refinement 2 (user follow-up) — Settings-driven defaults + strict-UP class closed
User: remove the on-screen Warehouse / Tax Template / Expense Account pickers from purchase
mode — make them defaults from the Settings screen only ("كقيم افتراضيه").

**Hide the pickers, source from Settings (`89603f6`):** purchase mode now shows only the
Supplier selector. `get_new_purchase_invoice_defaults` resolves the receiving warehouse to the
configured default, else the POS Profile's own warehouse (so purchases work day-one); tax
template / expense account stay opt-in (applied only when configured — no silent VAT/expense).
Frontend removed the three pickers + dead option-fetches (loadPurchaseMeta 5→2 calls), guard
now points at Settings. 25/25 vitest, build green.

**Strict user-permission class — root-caused and CLOSED (`fe53543` + `cf07333`):** verifying
the fallback path surfaced that a restricted cashier could not actually complete a purchase
(only the button *render* had ever been checked). Root cause is one class: this site runs
`apply_strict_user_permissions=1`, and each POS profile pins its cashier to a Company + a
Warehouse via User Permissions; strict mode then fails ANY empty Company/Warehouse Link field
checked per-document. Audited the whole Company/Warehouse link surface of the purchase-path
doctypes and shipped `ignore_user_permissions` Property Setters for the metadata/default links
only:
- `Warehouse.default_in_transit_warehouse` — empty receiving-warehouse dropdown (`fe53543`).
- `Item Default.default_warehouse` — blocked reading a purchasable item.
- `Item Reorder.warehouse` / `warehouse_group` — same Item-child class.
- `Purchase Invoice.represents_company` — empty inter-company marker blocked submit.
Real tenant boundaries stay UP-checked (Item.company multi-tenant scoping, Purchase Invoice
.company / set_warehouse, Purchase Invoice Item.warehouse — all populated in this flow).
**Verified live end-to-end as the Phones cashier: draft → submit (docstatus 1) → stock ledger
+1 into `Phones - Ph`.** Regression test extended with the Item per-doc case + shipped-setter
assertions. (`bench run-tests` itself is currently blocked by an unrelated erpnext test-record
bootstrap error — documented; verification was done live via the console harness.)
