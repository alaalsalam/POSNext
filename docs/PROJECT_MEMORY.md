# Digit POS Development Program — Project Memory

Last verified: 2026-08-01

This file is the durable memory and source of operational context for the Digit POS
development program. Read it before changing code, and update the progress section
after every completed milestone.

## Non-Negotiable Environment Boundary

| Environment | Site | Checkout | Branch | Verified commit | Policy |
|---|---|---|---|---|---|
| Production | `pos.digit-erp.com` | `/home/erpnext/frappe-bench-startd-prod/apps/posnext` | `digitpos` | `49c70f5` | Keep unchanged until an explicit, approved release |
| Development | `digitpos.trilogy-erp.com` | `/home/erpnext/frappe-bench16/apps/posnext` | `develop` | `2a39d82` | All new work happens here |

Never edit, build, migrate, restart, switch branches, or deploy in the production
bench while implementing the development backlog. Production is the protected Digit
demo baseline.

## Repository and Branch Policy

- Canonical repository: `https://github.com/YemenFrappe/posnext.git`.
- Use one long-lived development branch only: `develop`.
- Do not create feature branches for this program unless the user explicitly asks.
- Keep `main` as a stable integration/release reference; do not develop directly on it.
- Keep production on `digitpos` until a release is accepted explicitly.
- Make focused local commits on `develop`, one coherent milestone per commit.
- Do not push, merge to `main`, or deploy to production without explicit user approval.

## Application Identity

- Git checkout directory: `apps/posnext`.
- Frappe/Python app name: `pos_next`.
- These are the same application, not duplicate apps.
- Never use the archived production copy at
  `/home/erpnext/frappe-bench-startd-prod/archives/posnext-20260729`.

## Current Stable Capabilities

The existing application already supports the core sales lifecycle: shopping cart,
barcode and item search, multiple payment methods, partial payments, credit sales,
returns, drafts, shifts, EOD reconciliation, offline queue and sync architecture,
offers, coupons, simple one-use gift coupons, multi-currency calculations, printing,
role-aware permissions, responsive UI, Arabic/English localization, and PWA support.

Do not rewrite stable capabilities. Extend them behind explicit flags and preserve
backward compatibility.

## Existing Reports

The original app provides five working Frappe Desk reports:

1. Sales vs Shifts Report.
2. Cashier Performance Report.
3. Payments and Cash Control Report.
4. Inventory Impact and Fast Movers Report.
5. Offline Sync and System Health Report.

They were executed successfully on production on 2026-08-01. The first three returned
six shift rows, the inventory report returned 70 rows, and the offline report returned
zero rows because production currently has no Offline Invoice Sync records.

The in-POS dashboard added in commit `9573cef` is different from those reports. Its
ERPNext 16 datetime defect was corrected in the reports milestone: database queries use
`posting_date` and `posting_time`, and build a response-only datetime for display. It is
secure-off and available only to assigned, company-authorized managers after the
profile's `enable_pos_reports` flag is deliberately activated.

## Existing Hidden Management Modules

The following implementations pre-existed as hidden management modules and are now
controlled independently by persisted, secure-off POS Settings flags:

- Catalog and item management.
- Purchase invoices.
- Supplier payments.
- In-POS report dashboard.

The umbrella constant has been removed. A hidden UI element is not a security boundary;
backend permission and feature checks remain mandatory.

## Verified Production Configuration Snapshot

- 16 enabled POS Profiles.
- 16 profiles have payment methods, warehouses, item groups, and write-off settings.
- Currency currently demonstrated: SAR only, although the code supports conversion.
- Partial payments: enabled in all 16 POS Settings.
- Returns: enabled in all 16 POS Settings.
- Credit sales and customer-credit payment: enabled in two profiles.
- Silent print: disabled in all profiles.
- Negative stock: disabled in all profiles.
- Tax-inclusive pricing: enabled in one profile.
- Loyalty: disabled, and no active Loyalty Program exists.
- Default allowed UI languages: Arabic and English.

## Known Documentation/Capability Gaps

- No global F4, F8, F9, or Ctrl+S shortcuts.
- No real virtual-scrolling implementation.
- No split-bill workflow.
- Gift Card is a one-use coupon, not a stored-value ledger card.
- No manager approval workflow for credit-limit exceptions.
- No free-shipping promotion type.
- No native mobile app, restaurant/table/KDS mode, customer-facing display, integration
  hub, automatic restocking, or full ZATCA Phase 2 integration.
- The documented `pos_next.api.invoices.create_invoice` endpoint does not exist; the
  current flow is `update_invoice` followed by `submit_invoice`.

## Engineering Rules

1. Preserve the existing Digit visual identity and component patterns.
2. Arabic and English are mandatory for every new user-facing string and layout.
3. Every feature must be disabled by default until its acceptance suite passes.
4. Enforce flags and permissions on both frontend and backend.
5. Never use `ignore_permissions=True` as a substitute for a designed permission model.
6. Financial operations must be idempotent, auditable, and transaction-safe.
7. Offline changes must define conflict, retry, deduplication, and recovery behavior.
8. Schema changes require migrations or fixtures and rollback notes.
9. Avoid large rewrites; deliver vertical slices that can be tested independently.
10. A feature is not complete merely because UI code exists.

## Definition of Done

A feature is complete only when all applicable conditions are true:

- Requirements and accounting/data effects are documented.
- Backend permission and feature-flag enforcement exists.
- Frontend behavior is complete on desktop, tablet, and touch layouts.
- Arabic and English have been verified, including RTL.
- Unit/integration tests cover happy path, validation, permissions, and failure paths.
- Offline behavior is either implemented and tested or explicitly blocked safely.
- Build, lint/static checks, and relevant Frappe tests pass.
- Demo data and a repeatable manual acceptance scenario exist.
- Documentation and this memory file are updated.
- A focused commit records the milestone.

## Progress Ledger

| Milestone | Status | Evidence/commit | Notes |
|---|---|---|---|
| Program setup and durable planning | Completed | Planning baseline commit | Production protected; `develop` created |
| Feature flag foundation | Completed | `35194aa` | Four profile-scoped management flags; secure-off and manager-controlled |
| Reports compatibility and in-POS access | Completed | `2a39d82` | Manager-only, profile/company isolated, ERPNext-reconciled, five reports integrated |
| Catalog/purchases/supplier payments hardening | Completed | `8b5145d` | Manager/profile/company scoped; ERPNext GL/SLE/Payment Ledger acceptance passed |
| Offline end-to-end hardening | Not started | — | Must produce real sync records |
| Keyboard productivity | Not started | — | Quick, isolated milestone |
| Credit approval workflow | Not started | — | Accounting/permissions sensitive |
| Split bills | Not started | — | Requires offline/return design |
| Stored-value gift cards | Not started | — | Requires a ledger, not coupon reuse |
| Large-catalog virtual scrolling | Not started | — | Performance acceptance required |
| Loyalty activation | Not started | — | Depends on stable wallet/accounting |
| Quick restock | Not started | — | Depends on purchase workflow |
| External integrations and compliance | Not started | — | Provider/spec decisions required |
| Restaurant/native/customer display initiatives | Deferred | — | Separate product programs |

## Resume Protocol

At the start of every new development session:

1. Read this file and `docs/DEVELOPMENT_MASTER_PLAN.md` completely.
2. Confirm the current checkout is `/home/erpnext/frappe-bench16/apps/posnext`.
3. Confirm the branch is `develop` and the working tree state is understood.
4. Confirm production remains on `digitpos` and do not mutate it.
5. Continue the first incomplete milestone in the Progress Ledger.
6. Update the ledger before ending the session.

## Milestone Evidence — Feature Flag Foundation

Completed on 2026-08-01 in the development checkout only. Production was re-verified
unchanged on `digitpos` at `49c70f5` after implementation.

### Decisions and implementation

- Added independent `POS Settings` flags for catalog, purchases, supplier payments,
  and in-POS reports. All default to off; Supplier Payments requires Purchases.
- Removed `POSNext Cashier` write permission from `POS Settings`. The generic settings
  mutation API and profile warehouse mutation are manager-only. Non-Administrator
  access requires explicit POS Profile assignment plus POS Profile and Company user
  permission.
- Added `require_feature()` and applied it before document permissions on every public
  endpoint in the four management areas. Missing settings and invalid profiles fail
  closed.
- Reused native tracked Version history for actor/time/old/new audit evidence. Added
  session bootstrap flags and realtime invalidation of bootstrap, settings, and the
  shared frontend permission cache.
- Added a responsive manager Feature Flags tab using active-locale translation keys;
  Arabic translations are in `pos_next/translations/ar.csv` and layout remains
  direction-aware through existing RTL/LTR infrastructure.
- Detailed architecture, rollback, and manual acceptance are documented in
  `docs/FEATURE_FLAGS.md`.

### Verification evidence

- Development migration: `bench --site digitpos.trilogy-erp.com migrate` — passed.
- Runtime schema/default audit: all four fields present; all 16 POS Settings records
  remained `0`; runtime cashier DocPerm reports `write=0`.
- Python unit/API-negative suite: direct unittest, 14/14 passed.
- Frappe-connected console suite: feature flags plus supplier-payment regression,
  21/21 passed.
- Real development-user negative acceptance: `chocolates@trilogy.com.sa` was denied
  access to foreign profile `الألعاب` and denied mutation of `allow_credit_sale` on
  assigned profile `الشوكولاتة`; no data was changed.
- Frontend Vitest: `yarn test:run src/composables/usePermissions.test.js` — 2/2 passed.
- Python lint: `uvx ruff check <changed Python files>` — passed.
- Python compile, JSON validation, and `git diff --check` — passed.
- Targeted Biome lint for the new shared permission cache and test — passed.
- Development frontend build:
  `NODE_OPTIONS=--experimental-global-webcrypto yarn build` — passed.

### Known limitations and harness notes

- Standard `bench run-tests` discovery is blocked before selected tests run because
  the existing ERPNext test bootstrap attempts to insert duplicate `Standard Buying`
  Price List data. No user data was deleted to work around it. The same tests were run
  through a Frappe-initialized development-site console, which executed 21 tests
  successfully; the standalone flag suite also passed independently.
- Full Biome checking of legacy Vue files hits a known parser assertion and reports
  pre-existing style findings. Targeted JavaScript lint and the Vite Vue compilation
  passed; the milestone does not reformat unrelated legacy components.
- Duplicate PWA configuration keys were removed in the reports correction pass. Vite
  retains existing warnings for unresolved deployment-time Digit assets and mixed
  static/dynamic imports.
- Flags for later Master Plan milestones will be added with their accepted vertical
  slices; they remain unavailable rather than exposing inactive placeholder controls.

## Milestone Evidence — Reports Compatibility and In-POS Access

Completed on 2026-08-01 in the development checkout only. Production was re-verified
unchanged on `digitpos` at `49c70f5`; no production build, migration, restart, or write
was performed. All report flags on development remained off.

### Decisions and implementation

- Replaced invalid Sales Invoice `posting_datetime` queries with ERPNext 16
  `posting_date`/`posting_time` selection and ordering. Display datetimes are constructed
  only in the API response.
- Made the dashboard and every public/Desk report entry Manager-only, feature-guarded,
  and single-POS-Profile scoped. Profile assignment plus normal POS Profile, Company,
  reference DocType, and User Permissions are enforced; cashier and POS User roles do
  not gain report access through Sales Invoice read permission.
- Integrated links for all five existing Desk reports with the selected profile and
  resolved dates. Their filters require POS Profile, and the Sales vs Shifts report no
  longer grants its former standalone `POS User` role.
- Reconciled signed `grand_total` against `net_total + total_taxes_and_charges`, while
  reporting ERPNext rounding separately. Sales, returns, taxes, outstanding credit,
  payment tender, and recent invoices all come from submitted POS Sales Invoices only.
- Reworked the dashboard to use one active locale, direction-aware RTL/LTR, locale-aware
  formatting, English translation keys, and Arabic translations. Added responsive,
  touch-sized detailed-report links and a visible reconciliation state.
- Added the non-posting acceptance fixture
  `pos_next/tests/fixtures/reports_acceptance.json` and documented accounting/access
  semantics and acceptance in `docs/REPORTS.md`.

### Verification evidence

- Standard selected `bench run-tests` was attempted and stopped during ERPNext bootstrap
  at duplicate Price List `Standard Buying`, before loading the selected modules. No
  existing data was deleted or modified to bypass it.
- The exact report suites were run in a Frappe-initialized development console: 12/12
  passed, covering datetime compatibility, reconciliation, negative cashier access,
  direct flag enforcement, required profile, and profile/company exclusion.
- Real manager isolation on development: `manager.demo@digitpos.trilogy-erp.com` received
  no reportable profiles; assigned `Digit POS Main` was denied by Company permission and
  foreign `الجوالات` was denied by POS Profile assignment. No data changed.
- Direct API flag-negative acceptance on `الجوالات` returned `PermissionError: This POS
  feature is disabled`; all 16 development report flags remained `0`.
- Read-only reconciliation for `الجوالات` (2026-07-26 through 2026-07-30) matched direct
  ERPNext totals: grand 224,493.65; net 223,841.45; tax 652.20. ERPNext rounding of
  -6.65 is reported separately. The five report modules executed read-only with row
  counts 0, 2, 1, 45, and 0 for that scoped dataset.
- Frontend Vitest: 4/4 passed across permission-cache and report URL/RTL tests. Targeted
  Biome checking passed.
- Python compile, Ruff, JSON validation, `git diff --check`, and the development Vite
  build passed.

### Known limitations and harness notes

- The ERPNext duplicate-Price-List bootstrap blocker is pre-existing and remains exact;
  the Frappe-console alternative provides real framework/DB initialization without
  destructive test-record cleanup.
- Development acceptance used existing submitted records read-only and a non-posting
  fixture; no financial demo documents were inserted and no live profile was activated.
- The five reports can legitimately return zero rows when the selected profile/date has
  no closing-shift or offline-sync references. The dashboard does not aggregate across
  profiles by design.
- The successful Vite build retains pre-existing deployment-time Digit asset and
  static/dynamic chunk warnings. Duplicate PWA-key warnings were removed in the reports
  correction pass.

## Correction Evidence — Reports Post-Implementation Review

Completed on 2026-08-01 in development only. Production remained clean on `digitpos` at
`49c70f5`; no production or development migration/restart was performed, and every
development feature flag remained off.

### Root causes and corrections

- Bank-deposit rows selected `deposit_amount`/`deposit_date` but attempted to return the
  nonexistent `cnt`, and the helper was never called. The report now fetches deposits
  once per result set, merges them per shift, and supplies explicit `0`/`null` defaults.
- Datetime filters compared an end-date string at midnight. Closing-shift, cashier-shift,
  sales-vs-shifts, and offline-sync queries now use half-open datetime bounds; date-only
  invoice queries remain inclusive. Inventory depletion now uses `date_diff + 1`.
- Payment distribution excluded returns and overloaded one amount. It now reports
  received/refunded/net by method, period-level change, signed tender reconciliation,
  and the documented rounded invoice-balance equation across sales, returns, credit,
  partial/split tenders, write-off, and rounding.
- Dynamic payment fields now use deterministic, unique ASCII/hash identifiers instead
  of `lower().replace(" ", "_")`.
- The stale `run_reports_tests.py` was replaced with a non-destructive unittest runner
  that loads the current APIs and propagates failure through its process exit code.
- Three duplicate Workbox keys were genuinely pre-existing (introduced in different
  historical commits). The redundant later definitions were safely removed in a
  separate config-only commit `90da153`; behavior is unchanged because both values were
  identical.

### Verification evidence

- Repeatable backend command: `../../env/bin/python run_reports_tests.py` — 19/19 passed,
  exit code 0. It covers deposits absent/present/multiple, batch/no-N+1 behavior,
  last-second and one-day dates, safe dynamic fields, payment scenarios, permissions,
  flags, and profile/company isolation.
- Real read-only `الجوالات` acceptance: received 237,864.00; refunded 3,826.00; signed
  tender and ERPNext paid amount both 234,038.00 (`tender_difference = 0`). Current
  invoice-balance difference is visibly 1,050.00, traced to three historical invoices
  whose negative outstanding changed after their original POS tender; it is not claimed
  as reconciled.
- Payments and Cash Control executed on the development dataset and returned one shift
  with the explicit no-deposit defaults. No submitted Bank Deposit currently exists, so
  valid/multiple deposit merging is covered by the batch-query regression tests.
- Real permission acceptance was repeated: the demo manager was denied its assigned
  profile by Company permission and denied foreign `الجوالات` by profile assignment;
  the cashier was denied by the manager-role gate; Administrator was denied direct API
  access by the off report flag. Sums for all four flags across all settings were zero.
- Targeted Biome passed and Vitest passed 4/4. The development Vite build passed without
  the former duplicate Workbox-key warnings; remaining warnings are the documented
  deployment-time assets, third-party pure annotations, and mixed imports.
- Python compile, Ruff, JSON/diff validation, and `git diff --check` passed. The standard
  selected `bench run-tests` command was reattempted and failed before test loading at
  the same duplicate `Standard Buying` ERPNext bootstrap record.

## Milestone Evidence — Catalog, Purchases, and Supplier Payments Hardening

Completed on 2026-08-01 in development commit `8b5145d`. Production was read-only
verified before work as clean on protected branch `digitpos` at `49c70f5`; it was not
built, migrated, restarted, written, pushed, merged, or deployed.

### Decisions and implementation

- Reused ERPNext Item/Item Group/Item Price, Supplier, Purchase Invoice, Payment Entry,
  GL Entry, Payment Ledger Entry, and Stock Ledger Entry controllers. No ledger or stock
  row is created manually.
- Added a shared manager/profile/company guard and applied explicit POS Profile scope,
  normal document permissions, and User Permissions to every catalog, purchase, and
  supplier-payment endpoint. Cashier bootstrap permissions and direct calls fail closed.
- Catalog now validates group hierarchy, UOM, stock settings, barcode uniqueness, scoped
  price lists/currencies/validity, and idempotent Item Price identity. Misleading quick
  opening stock is rejected.
- Purchase Invoice uses allow-listed headers/items/taxes, scoped linked resources,
  durable retry keys, stale-draft detection, row locks, and native draft/submit/cancel.
  UI supports supplier creation, tax templates, expense accounts, stock warehouse,
  currency/exchange rates, totals, status, and history.
- Supplier Payment uses native Payment Entry with one exact Purchase Invoice allocation,
  positive/no-overpay validation, unique retry key, locked outstanding recheck,
  savepoint rollback, standard submit/cancel, and batch-loaded allocation history.
- Added responsive active-locale Arabic/English manager UI with independent
  read/create/write/submit/cancel controls, confirmation, safe errors, and double-action
  prevention. Detailed design and rollback semantics are in
  `docs/CATALOG_PURCHASES_PAYMENTS.md`.

### Schema and data safety

- Development backup before schema:
  `sites/digitpos.trilogy-erp.com/private/backups/20260801_173532-digitpos_trilogy-erp_com-database.sql.gz`.
- `bench --site digitpos.trilogy-erp.com migrate` passed for the custom fields; a second
  development-only migrate applied DocPerm fixtures. No restart was performed.
- Acceptance used unique `POSNEXT-QA-*` documents/users in one uncommitted transaction.
  Standard cancellations were exercised, then the entire QA transaction was rolled
  back. No persistent financial or catalog QA data remains.
- The runner temporarily enabled only the selected QA profile inside that transaction.
  Final values were catalog `0`, purchases `0`, supplier payments `0`.

### Verification evidence

- Repeatable backend runner:
  `/home/erpnext/frappe-bench16/env/bin/python run_milestone2_tests.py` — 36/36 passed.
- Selected standard Frappe tests passed normally on the development site:
  `test_feature_flags` 14/14, `test_management_hardening` 15/15, and
  `test_supplier_payments` 7/7. The prior Standard Buying bootstrap failure did not
  recur for these selected modules; no data was deleted to influence the result.
- Real acceptance:
  `/home/erpnext/frappe-bench16/env/bin/python apps/posnext/run_milestone2_acceptance.py`
  — passed with rollback. It covered manager/cashier and foreign-profile denial,
  catalog prices/barcode/idempotency, tax, no-stock and update-stock purchases, USD
  currency, partial/full payment, duplicate/concurrent guards, and cancellations.
- Accounting evidence: six balanced GL rows across the measured purchases; stock SLE
  quantity `3` before cancellation and no active effect afterward; Purchase Invoice
  outstanding `18`, then `9` after partial payment, then `0` after full payment, and
  restored to `18` after cancelling both Payment Entries. Payment Ledger allocations
  and Purchase Invoice outstanding agreed at each boundary.
- `yarn test:run` — 4 files/8 tests passed. Targeted Biome passed. Development build
  with `NODE_OPTIONS=--experimental-global-webcrypto yarn build` passed with 2,192
  modules. Ruff, Python compile, JSON validation, and `git diff --check` passed.

### Known limitations

- Supplier payment allocation is deliberately one Purchase Invoice per manager action;
  multi-invoice allocation and advances remain disabled.
- Quick catalog opening stock remains disabled; it requires a separate standard stock
  workflow rather than hidden ledger creation.
- Node 18 needs the Web Crypto option for this Vite build. Existing deployment-time
  asset and mixed-import warnings remain non-fatal technical debt.
- ERPNext emitted its upstream v16 stock-controller deprecation warning during real
  acceptance; GL/SLE/Payment Ledger reconciliation still passed.

## Correction Evidence — Milestone 2 Post-Acceptance Review

Completed on 2026-08-02 in development commit `8f4a067`. Production was re-verified
unchanged on clean branch `digitpos` at `49c70f5`; no production build, migration,
restart, write, push, merge, or deployment occurred. Milestone 3 was not started.

### Idempotency correction

- Added hidden, read-only SHA-256 request fingerprints to Purchase Invoice and Payment
  Entry. They are stored beside the unique idempotency key and refreshed when a purchase
  draft is legitimately updated.
- Canonical purchase binding covers all accepted header, date, discount, currency/rate,
  account, warehouse, remarks, item, cost-center, tax-template, and tax-row inputs after
  server defaults and validation. Dates and Decimal numbers are normalized; object keys
  are sorted; child positions remain explicit because sequential taxes are order-sensitive.
- Payment binding covers profile/company, invoice, amount, account, posting/reference
  dates, mode, reference number, and remarks. Submit intent is excluded intentionally,
  preserving an exact retry that promotes the same existing draft to submitted.
- Missing legacy fingerprints and changed material requests fail closed with
  `ValidationError`; neither API silently returns an old document for a different request.

### Schema and data safety

- Development backup:
  `sites/digitpos.trilogy-erp.com/private/backups/20260802_010919-digitpos_trilogy-erp_com-database.sql.gz`.
- `bench --site digitpos.trilogy-erp.com migrate` completed successfully on the named
  development site only. No restart was used.
- Transactional ERPNext acceptance again rolled back every `POSNEXT-QA-*` user, master,
  and financial document. Flags after rollback were catalog `0`, purchases `0`, and
  supplier payments `0`.

### Concurrency evidence and limitation

- `run_milestone2_concurrency.py` used two distinct MariaDB connection IDs and two real
  InnoDB transactions. Both attempted to consume the full outstanding `100`. One
  committed one allocation; the other waited `0.756s` on the row lock, then observed
  outstanding `0` and was rejected. Final state was outstanding `0`, allocated `100`,
  one allocation row, and no negative balance. Its uniquely named QA table was dropped
  in `finally`.
- This proves the database locking/atomic-recheck invariant, not simultaneous execution
  of two ERPNext Payment Entry controllers. Rollback-only QA documents are invisible to
  independent connections; committing temporary financial documents just to race them
  was rejected as an unnecessary data-safety regression. The separate real ERPNext
  acceptance proves GL, Payment Ledger, cancellation, and outstanding behavior.

### Verification evidence

- `/home/erpnext/frappe-bench16/env/bin/python run_milestone2_tests.py` — 40/40 passed.
- Standard Frappe suites: feature flags 14/14, management hardening 16/16, supplier
  payments 10/10.
- `run_milestone2_acceptance.py` — passed with six balanced GL rows, SLE quantity `3`,
  outstanding `18 → 9 → 0 → 18`, conflict-negative retries, cancellations, and rollback.
- `run_milestone2_concurrency.py` — passed with the two-transaction evidence above and
  all three management flag sums at zero.
- Frontend `yarn test:run` — 6 files/13 tests passed. Added behavior tests for catalog
  payload/in-flight blocking and Purchase Invoice stable key, `expected_modified`,
  save/submit blocking, permission-controlled cancellation, and stale reload state.
- Ruff, Python compile, JSON validation, targeted Biome, `git diff --check`, and the
  development Vite build passed. Vite transformed 2,192 modules; only the previously
  documented runtime asset and mixed-import warnings remain.
