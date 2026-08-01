# Catalog, Purchases, and Supplier Payments

## Scope and audit baseline

Milestone 2 hardens the existing manager-only catalog and buying screens. It does not
replace ERPNext buying or accounting controllers. All three feature flags are secure-off
per POS Profile. Every request carries an explicit POS Profile and is rejected when the
profile, its company, the document, or a linked resource is outside the current user's
permissions.

The pre-hardening audit found reusable standard document flows for Item, Item Group,
Item Price, Supplier, Purchase Invoice, and Payment Entry. Purchase Invoice and Payment
Entry already used native `save`, `submit`, and `cancel`, which are retained. The gaps
were unrestricted document dictionaries, permission-bypassing `get_all` queries,
implicit active-profile resolution, hard-coded price lists, incomplete resource checks,
no durable retry keys, no stale-draft protection, and no atomic outstanding recheck.
The catalog `opening_qty` input did not create stock and was therefore misleading.

## Data model and ownership

- Catalog uses ERPNext Item Group, Item, Item Barcode, UOM, Price List, and Item Price.
  Item Price identity is item + price list + UOM + validity window. Ambiguous existing
  duplicates are rejected rather than silently overwritten.
- Suppliers remain global ERPNext Supplier masters. Supplier and Supplier Group document
  permissions and User Permissions are enforced. A supplier becomes company-scoped when
  used by a Purchase Invoice in the selected profile company.
- Purchases use Purchase Invoice and its standard item/tax child tables. Two internal,
  read-only fields record the originating POS Profile and a unique client idempotency key.
- Supplier payments use Payment Entry and Payment Entry Reference. The same two internal
  fields provide profile lineage and a unique retry key. Advances are not exposed.

## Permission and scope rules

The server is the authority; hiding buttons is only a UX aid. `catalog`, `purchases`, and
`supplier_payments` are checked independently with the explicit POS Profile. The user
must be assigned to that profile and retain Company and DocType permissions. Cashiers
are denied by feature-manager/API permissions even if they call endpoints directly.

Company-linked resources must match the profile company. Warehouses and Accounts must
be non-group, enabled, readable documents in that company. Selling catalog prices are
restricted to the profile selling price list; buying prices default to ERPNext 16 Buying
Settings and require a buying-enabled, readable Price List. Items, Item Groups,
Suppliers, UOMs, currencies, Modes of Payment, and transaction documents are checked as
documents, preserving ERPNext User Permissions. List APIs use permission-aware queries.

## Stock, accounting, tax, and currency effects

Catalog changes have no GL or Stock Ledger effect. Opening stock is intentionally not
supported by the quick-create endpoint; non-zero `opening_qty` is rejected. Stock must
enter through a standard stock transaction with its own audit and reversal flow.

Purchase Invoice is the only purchase posting controller:

- `update_stock = 0`: ERPNext posts payable, expense/asset, and tax GL entries; no Stock
  Ledger Entry is created.
- `update_stock = 1`: ERPNext additionally posts stock receipt/valuation through its
  standard controller and creates the corresponding stock accounting entries.
- Submit is the posting boundary. Cancel invokes ERPNext cancellation and reverses GL,
  Payment Ledger, and Stock Ledger effects as applicable. Submitted/cancelled documents
  cannot be edited by these APIs.
- Tax rows are allow-listed and validated by ERPNext. Account, cost center, and company
  scope are checked before save. Totals returned by the API are controller-calculated.
- Company currency is the default. A foreign invoice requires a valid currency and a
  positive conversion rate; ERPNext owns exchange-rate and base-total calculation.

Payment Entry is the only supplier-payment posting controller. Drafts have no ledger
effect. Submit debits payable, credits the selected cash/bank account, creates Payment
Ledger effects, and reduces Purchase Invoice outstanding. Cancel reverses those effects.
Amounts must be positive and cannot exceed the locked, current invoice outstanding.

## Idempotency, concurrency, and failure recovery

New Purchase Invoice and Payment Entry requests require a client-generated idempotency
key. A database-unique custom field makes retries durable and race-safe. A retry with the
same key returns the original document only when profile/company and request ownership
match; key reuse for a different operation is rejected.

Draft updates require `expected_modified`. The server locks the row and rejects stale
clients before applying an allow-listed payload. Submit/cancel operations lock their
document. Supplier-payment creation and submission also lock the referenced Purchase
Invoice row, reload outstanding, and revalidate allocation before posting. This serializes
double clicks and competing payments. Savepoints roll back a failed create/submit so the
API does not leave a hidden partial document. Native ERPNext validation errors remain
user-safe; unexpected failures are logged with an Error ID.

Payment allocation is limited to one Purchase Invoice per manager action in this slice.
Partial and full payments are supported; overpayment and implicit advances are disabled.
Multiple-invoice allocation remains a documented future extension rather than an unsafe
partial implementation.

## UI and acceptance contract

The existing Digit manager workspace is retained. All calls pass the active profile.
Buttons follow read/create/write/submit/cancel permissions, financial actions require
confirmation, and in-flight state prevents double submission. Text uses translation keys,
the active locale only, logical start/end layout, responsive panels, and touch-sized
controls. Loading, empty, validation, and safe error states are explicit.

Acceptance must cover flag-off and cashier bypass attempts; foreign profile/company/
warehouse/account/price-list/supplier denial; catalog duplicate/idempotent paths; purchase
draft/update/submit/cancel including taxes and stock; and payment partial/full/retry/
concurrent/cancel. Real development-site acceptance reconciles Purchase Invoice totals
and outstanding with GL, Payment Ledger, and Stock Ledger. QA documents are uniquely
prefixed and cancelled through normal ERPNext workflows. No production data is used.

## Milestone 2 implementation evidence

Completed in the development checkout on 2026-08-01. The audit reused ERPNext Item,
Item Price, Purchase Invoice, Payment Entry, GL, Payment Ledger, and Stock Ledger
controllers. It fixed the existing implicit-profile access, mass assignment, misleading
opening-stock input, hard-coded price assumptions, stale-write exposure, retry duplication,
and non-atomic supplier-payment allocation. Newly implemented pieces are the shared
manager/company scope guard, durable profile/idempotency fields, complete scoped APIs,
permission-specific manager UI, active-locale translations, and non-destructive runners.

Before adding the two custom-field schemas, the development site only was backed up to:

`sites/digitpos.trilogy-erp.com/private/backups/20260801_173532-digitpos_trilogy-erp_com-database.sql.gz`

`bench --site digitpos.trilogy-erp.com migrate` completed successfully. A second
development-only migrate applied the permission fixtures. No production migration,
build, restart, or write was performed.

Repeatable verification commands and final results:

- `/home/erpnext/frappe-bench16/env/bin/python run_milestone2_tests.py` — 36/36 passed.
- `bench --site digitpos.trilogy-erp.com run-tests --app pos_next --module
  pos_next.tests.test_feature_flags` — 14/14 passed.
- The same command for `test_management_hardening` — 15/15 passed; for
  `test_supplier_payments` — 7/7 passed.
- `/home/erpnext/frappe-bench16/env/bin/python
  apps/posnext/run_milestone2_acceptance.py` — passed with rollback. It created a
  non-stock invoice, a stock invoice, a USD invoice, partial/full payments, and standard
  cancellations inside an uncommitted QA transaction.
- Acceptance measured six GL entries, stock quantity `3`, initial outstanding `18`,
  outstanding `9` after the partial payment, and `18` after payment cancellation. It
  verified balanced GL, Payment Ledger allocations, active/cancelled Stock Ledger state,
  manager/cashier denial, and foreign-profile denial.
- `yarn test:run` — 4 files, 8 tests passed. Selected Biome checks passed.
- `NODE_OPTIONS=--experimental-global-webcrypto yarn build` — development build passed,
  2,192 modules transformed. Node 18 requires the Web Crypto option; runtime asset and
  mixed-import warnings predate this milestone and remain non-fatal technical debt.
- Ruff, Python compile, JSON parsing, and `git diff --check` passed.

The acceptance runner temporarily changes flags only inside its database transaction,
then rolls it back. Its final check returned catalog, purchases, and supplier-payments
flags as `0`. QA users and documents were likewise rolled back; no permanent financial
transaction remains.

## Known limitations

- One manager payment action allocates one Purchase Invoice. Multi-invoice allocation
  and supplier advances remain intentionally disabled.
- Quick catalog creation does not establish opening stock; managers must use a standard
  ERPNext stock transaction outside this slice.
- The development runtime emits an ERPNext 16 stock-controller deprecation warning from
  upstream code. It did not affect GL/SLE reconciliation.
- Vite reports existing unresolved Digit/demo asset references and mixed static/dynamic
  imports. The build succeeds, and these warnings are tracked as technical debt rather
  than mixed into the accounting change.
