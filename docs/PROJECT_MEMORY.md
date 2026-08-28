# Digit POS Development Program — Project Memory

Last verified: 2026-08-20

This file is the durable memory and source of operational context for the Digit POS
development program. Read it before changing code, and update the progress section
after every completed milestone.

## YemenFrappe Canonical Deployment (2026-08-03)

- Canonical repository: `https://github.com/YemenFrappe/posnext.git`.
- Canonical long-lived branch: `develop`.
- Deployment site: `pos.yemenfrappe.com` in `/home/frappe/frappe-bench`.
- The YemenFrappe `develop` history is the base; legacy Maward/offline fixes are
  selectively ported onto it. Do not replace it with the old `maward-version` history.
- Pre-integration deployed revision: `cbe9397`, preserved locally as
  `backup/maward-version-before-yemenfrappe-integration-20260803`.
- Integration base: upstream YemenFrappe `develop` revision `0e957e3`.
- The detailed integration inventory, validation, and rollback contract is recorded in
  [`YEMENFRAPPE_CANONICAL_BASELINE.md`](YEMENFRAPPE_CANONICAL_BASELINE.md).

The Digit production/development boundaries below are retained as historical program
context. They do not supersede the YemenFrappe deployment boundary above.

## Non-Negotiable Environment Boundary

| Environment | Site | Checkout | Branch | Verified commit | Policy |
|---|---|---|---|---|---|
| Production | `pos.digit-erp.com` | `/home/erpnext/frappe-bench-startd-prod/apps/posnext` | `digitpos` | `49c70f5` | Keep unchanged until an explicit, approved release |
| Development | `digitpos.trilogy-erp.com` | `/home/erpnext/frappe-bench16/apps/posnext` | `develop` | `5249fe5` | Milestone 2 accepted baseline plus post-acceptance correction evidence |

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
| Catalog/purchases/supplier payments hardening | Completed | `8b5145d`, `8f4a067`, `5249fe5` | Accepted workflow plus full retry binding, locking evidence, and durable documentation |
| POS Desk workspace navigation | Completed | Local workspace/sidebar patch, 2026-08-20 | Frappe v16 app-owned sidebar with six RTL-translated sections, 39 permission-filtered entries, a branded colored POS icon, and a professional workspace home. The home now shows a permission-scoped account overview (today's sales, monthly net sales, returns, open shifts, and recent invoices) followed by native operational and financial cards. |
| POS stock integrity and availability | Completed | `pos.yemenfrappe.com`, 2026-08-20 | POS pre-submission validation now reads the stock ledger rather than the Bin cache; zero/negative items are blocked from the cart, 2,183 ordinary POS item/warehouse pairs were reconciled to 20 units, and three serial/batch items were deliberately left for controlled serial/batch setup. Negative stock was enabled only during the historical-ledger repair and restored to disabled. |
| POS WhatsApp invoice delivery | Completed | `pos.yemenfrappe.com`, 2026-08-20 | Automatic invoice delivery now renders internal attachments under the system account while restoring the cashier session afterwards, so POS staff do not need broad Conversations permissions. The Sales Invoice scenario uses the dedicated `POS WhatsApp Invoice` PDF format. Each automation now decides whether it applies the sending policy; transactional automations default to direct delivery with the policy off, while campaigns explicitly opt in to managed pacing. |
| POS invoice print formats | Completed | `pos.yemenfrappe.com`, 2026-08-20 | `POS Next Receipt` is a high-contrast 80 mm thermal receipt with customer mobile, paid/balance/return status, accurate discounted item totals, payment and warranty/serial details. `POS WhatsApp Invoice` is a branded A4 PDF with store-logo fallback, payment status, customer and item/IMEI detail, totals, and tax QR; it is the active automatic WhatsApp format. Both rendered successfully from `ACC-SINV-2026-00113`; the WhatsApp PDF is 136 KB. |
| Offline end-to-end hardening | Integrated baseline | `6b26a64` | Deployed on YemenFrappe; full transactional browser acceptance remains a separate QA milestone |
| Keyboard productivity | Not started | — | Quick, isolated milestone |
| Credit approval workflow | Not started | — | Accounting/permissions sensitive |
| Split bills | Not started | — | Requires offline/return design |
| Stored-value gift cards | Not started | — | Requires a ledger, not coupon reuse |
| Large-catalog virtual scrolling | Not started | — | Performance acceptance required |
| Loyalty activation | Not started | — | Depends on stable wallet/accounting |
| Quick restock | Not started | — | Depends on purchase workflow |
| External integrations and compliance | Not started | — | Provider/spec decisions required |
| Restaurant/native/customer display initiatives | Deferred | — | Separate product programs |

## Remaining Development Roadmap after Milestone 2

This section is the executable roadmap for future sessions. The authoritative delivery
rules, common testing layers, and milestone execution loop remain in
[`DEVELOPMENT_MASTER_PLAN.md`](DEVELOPMENT_MASTER_PLAN.md); this section adds durable
implementation context and acceptance detail without replacing that plan. The execution
order below reconciles exactly with its Priority Order.

The Master Plan lists future flags as target architecture. Only the four accepted
Milestone 0 flags currently exist. A future flag named below must be added, migrated,
permission-tested, and left secure-off as part of its own milestone; its presence in the
Master Plan is not evidence of implemented functionality. Offline is the one special
case: a queue/PWA architecture already exists in the stable sales path, while the Master
Plan defines no new offline-hardening flag. Preserve that path and gate only materially
new sync/recovery behavior behind a new secure-off, profile-scoped rollout flag if the
fresh audit shows a flag is necessary. Do not disable working offline sales merely to
fit the flag model.

### Milestone 3 — Offline end-to-end integrity

- **Business outcome:** cashiers can sell through a network outage and managers can
  recover every queued transaction without duplicate invoices, duplicate payments, lost
  audit evidence, or unexplained shift totals.
- **Baseline versus missing:** reuse the existing PWA/service-worker, local offline queue,
  invoice submission flow, and Offline Invoice Sync DocType/report. The architecture is
  present but real multi-invoice outage/reconnect acceptance, durable recovery UI, and
  successful Offline Invoice Sync evidence are not yet proven; production previously had
  zero Offline Invoice Sync records.
- **Dependencies and flag:** depends on stable sales, payments, shifts, returns, printing,
  feature/session bootstrap, and profile/company permissions. Audit existing offline
  settings first. If new worker/recovery behavior changes the active path, add a
  manager-controlled `enable_offline_hardening` profile flag through the normal secure-off
  migration process; otherwise document why no new flag is needed.
- **Backend/data/offline risks:** IndexedDB schema upgrades, browser eviction, stale price/
  stock/customer/payment-mode/promotion data, closed or changed shifts, clock/timezone
  drift, partial payment submission, service-worker version skew, and partial server
  failure can strand or reorder transactions.
- **Required controls:** persist each queued request in IndexedDB before success is shown;
  assign one durable client UUID/idempotency key that survives refresh/restart; preserve
  FIFO ordering per shift while allowing explicitly safe independent work; use background/
  service-worker sync with bounded exponential backoff and jitter; atomically claim queue
  work; deduplicate client and server side; define conflict policy for every stale entity;
  record partial failure stages; never silently discard; make recovery/retry idempotent;
  and keep printed-before-sync warnings and immutable audit timestamps.
- **Arabic/English UX:** one active locale, RTL/LTR logical layout, touch-sized pending/
  failed/conflict/retrying states, queue count, last successful sync, reason and safe next
  action, explicit shift mismatch handling, and accessible recovery confirmation.
- **Automated/manual acceptance:** unit tests for queue state, ordering, backoff, UUID
  persistence and conflict decisions; frontend IndexedDB/store/service-worker tests;
  direct API duplicate/permission tests; browser scenarios for offline launch, multiple
  queued cash/card/partial/credit/return invoices, refresh/restart, version upgrade,
  reconnection, repeated retry and partial failure. Create real development Offline
  Invoice Sync records and reconcile the health report, submitted invoices, payments,
  shift totals and queue state. Verify no duplicate Sales Invoice/Payment Entry.
- **Definition of Done:** deterministic conflict matrix and recovery runbook documented;
  real successful and failed/recovered sync records exist in disposable QA acceptance;
  health report evidence reconciles; flags/settings return to their prior state; all
  offline/browser/Frappe/regression/build checks pass; focused local commits and memory
  evidence exist. Stop for review before Milestone 4.
- **External decision/blocker:** none expected for core retail offline behavior. If product
  owners want offline credit approval, offline gift value, or provider payments, block
  only that sub-scenario until its later policy/credential milestone.

### Milestone 4 — Keyboard productivity

- **Business outcome:** trained cashiers complete common sales actions quickly without
  breaking touch, scanner, modal, or accessibility behavior.
- **Baseline versus missing:** reuse existing search, checkout, draft and modal actions;
  global F4/F8/F9/Ctrl-or-Cmd+S handling and a shortcut-help overlay are missing.
- **Dependencies and flag:** requires accepted core sale UX and Offline milestone
  regression stability; add `enable_keyboard_shortcuts` as a secure-off profile flag.
- **Risks and controls:** prevent shortcuts inside editable/contenteditable fields, IME
  composition, browser/system-reserved combinations, and incompatible modal focus.
  Centralize registration/cleanup, make dispatch single-fire and idempotent, and enforce
  the same backend permissions as pointer-triggered actions.
- **Arabic/English UX:** localized key names/help, logical RTL/LTR overlay, visible focus,
  screen-reader labels, Escape ownership, desktop hints without degrading touch layouts.
- **Acceptance:** component/event tests for every key, Mac/Windows modifiers, held keys,
  input/IME/modal suppression and cleanup; manual desktop/scanner/browser checks in both
  languages plus regression of touch checkout and offline queueing.
- **Definition of Done:** shortcuts work only in valid contexts, help is discoverable and
  accessible, flag/API-negative/regression/build checks pass, docs and focused commit are
  complete.
- **External decision/blocker:** confirm only if deployed browser/OS reserves a proposed
  key; otherwise use the Master Plan mapping without guessing a conflicting replacement.

### Milestone 5 — Credit approval workflow

- **Business outcome:** credit-limit or overdue exceptions require traceable manager
  approval while ordinary permitted credit sales remain fast.
- **Baseline versus missing:** credit sales/customer-credit payment exist for selected
  profiles; there is no exception policy engine, re-auth/PIN approval, decision record,
  or exception reporting.
- **Dependencies and flag:** requires Offline integrity, customer/company permissions,
  existing credit settings and receivable reporting; add `enable_credit_approval`, which
  must also require credit sales to be configured.
- **Accounting/reversal invariants:** submitted Sales Invoice receivable and customer
  exposure must equal ERPNext; approval never posts GL itself; submit re-evaluates current
  credit limit, overdue and open exposure atomically; returns, payments and cancellations
  reverse/reduce exposure through standard controllers; rejected/expired approvals post
  nothing.
- **Security/idempotency/concurrency:** manager re-authentication cannot be cached as a
  reusable secret; approval is profile/company/customer/request scoped, time-bound and
  single-use; direct API and stale approval bypass are denied; simultaneous invoices lock
  or atomically recheck exposure; approve/reject and invoice submission are idempotent and
  fully audited.
- **Arabic/English UX:** localized policy explanation, exposure/limit/overdue values,
  approve/reject reason, masked re-auth input, RTL/LTR, touch and accessible error states.
- **Acceptance:** policy unit tests; Frappe tests for limit, overdue, permission, stale and
  concurrent submissions; real QA invoice/payment/return/cancel reconciliation; offline
  behavior must fail safely unless an explicit offline-credit policy is approved; manual
  cashier/manager journeys in both languages.
- **Definition of Done:** no bypass, exposure reconciles before/after every reversal,
  approval audit is reportable, flag remains off after acceptance, all test/build layers
  pass, local commit and evidence recorded.
- **External decision/blocker:** product owner must choose thresholds, approval lifetime,
  re-auth method and whether any offline exception is allowed; do not invent them.

### Milestone 6 — Split bills

- **Business outcome:** a cashier can split one sale by items, quantities, equal amounts
  or custom amounts while preserving exact tax, discount, payment, print and return
  lineage.
- **Baseline versus missing:** cart, multiple/partial payments, invoices, returns and
  printing are reusable; parent split session, allocation engine and child lineage do not
  exist.
- **Dependencies and flag:** requires Offline integrity and stable credit approval rules;
  add `enable_split_bills` as a secure-off profile flag.
- **Accounting/reversal invariants:** sum of child net, tax, discount, rounding, grand
  total and tenders must equal the original allocation exactly within currency precision;
  never hide mismatch in write-off/rounding; free items and inclusive taxes retain source
  lineage; return/cancel reverses only eligible child quantities/payments without double
  reversal; shift attribution remains complete.
- **Security/idempotency/concurrency:** server validates allocation and ownership; one
  durable split-session UUID plus deterministic child keys; lock the session during
  finalize/cancel; repeated finalize returns the same children; partial failure resumes
  safely; direct API cannot modify finalized sessions.
- **Arabic/English UX:** responsive/touch split editor, RTL/LTR drag/quantity controls,
  remaining amount visibility, accessible validation, child receipts and clear recovery.
- **Acceptance:** allocation/property tests across taxes, discounts, free items, currencies
  and rounding; Frappe ledger/payment/return tests; two-client finalize race; offline
  queue/reconnect/order scenarios; manual split methods and reprint/return in both locales.
- **Definition of Done:** exact reconciliation and lineage proven, partial failure and
  reversal tested, flag off, docs/build/regressions and focused commit complete.
- **External decision/blocker:** product must decide whether restaurant-style seat/table
  splitting belongs here; default scope is retail bills only.

### Milestone 7 — Stored-value gift cards

- **Business outcome:** issue and redeem genuine stored value with a trustworthy balance,
  independently from existing one-use promotional Gift Card coupons.
- **Baseline versus missing:** reuse customer/payment/printing/audit patterns; the existing
  coupon is not stored value. Dedicated card master, immutable transaction ledger,
  liability accounting and lifecycle are missing.
- **Dependencies and flag:** requires Offline integrity and split/payment allocation
  stability; add company-scoped `enable_stored_value_gift_cards`; never relabel coupons.
- **Accounting/reversal invariants:** issue/top-up increases cash/receivable and gift-card
  liability, not revenue; redemption reduces liability against the sale; refund/cancel
  posts an exact compensating ledger transaction, never edits history; expiry/breakage is
  posted only under an approved policy/account; card balance equals immutable ledger sum
  and GL liability reconciliation.
- **Security/idempotency/concurrency:** unpredictable token plus optional barcode, never
  expose secrets in logs; company scope and manager permissions for issue/freeze; atomic
  balance lock; durable operation keys; concurrent redemption cannot overspend; lifecycle
  and failed/reversed operations are audited.
- **Arabic/English UX:** separate “promotional coupon” versus “stored value” labels,
  masked code, balance/history/status, accessible scanner/manual entry, RTL/LTR and clear
  online/offline availability.
- **Acceptance:** ledger calculation/property tests; concurrent redeem/top-up; API flag/
  permission negatives; real issue/partial/full redeem/refund/freeze/expire/cancel GL
  reconciliation; split bill and return integration; manual bilingual receipts/history.
- **Definition of Done:** immutable ledger and GL liability reconcile, no overspend or
  coupon ambiguity, approved offline policy enforced, flag off, tests/docs/build/commit.
- **External decision/blocker:** accounting must select liability, breakage/expiry, tax,
  refund and dormancy policy; product must decide whether offline redemption is forbidden
  or bounded. Do not guess either.

### Milestone 8 — Large-catalog virtual scrolling and performance

- **Business outcome:** 10k–50k item catalogs remain responsive on desktop and constrained
  tablets without losing search, scanner or accessibility behavior.
- **Baseline versus missing:** current item search/grid/list, lazy assets and catalog API
  are reusable; configuration thresholds are not real virtualization and no accepted
  performance budgets/benchmarks exist.
- **Dependencies and flag:** depends on Offline/catalog data paths and stable keyboard
  focus behavior. The Master Plan defines no flag; add a secure-off
  `enable_large_catalog_virtualization` profile rollout flag only if the implementation
  changes rendering behavior materially, otherwise document a transparent safe rollout.
- **Risks and controls:** memory growth, stale cached pages, item-height drift, RTL scroll,
  image churn, lost focus and barcode/search races. Use deterministic paging/cache keys,
  cancellation of stale requests, bounded caches and measurable budgets; no financial
  or ledger effect.
- **Arabic/English UX:** preserve RTL/LTR grid/list, keyboard focus, touch targets, empty/
  loading/error states, Arabic search and accessible virtualized position semantics.
- **Acceptance:** synthetic 10k and 50k datasets; automated render/search/memory/scroll
  measurements on desktop and constrained tablet profiles; regression for scanner,
  filters, images, offline cache and keyboard; manual long-scroll/focus checks both locales.
- **Definition of Done:** explicit initial-render, search latency, memory and smoothness
  budgets are met reproducibly, no behavior regression, rollout decision/flag documented,
  tests/build/profile evidence and focused commit complete.
- **External decision/blocker:** product/QA must approve numerical performance budgets and
  representative target devices before completion claims.

### Milestone 9 — Loyalty activation

- **Business outcome:** configured customers earn, redeem, reverse and understand loyalty
  points consistently across sales and returns.
- **Baseline versus missing:** ERPNext Loyalty Program support and existing customer/sale
  flows are reusable, but no active Loyalty Program exists and the Digit UI is disabled;
  tier/wallet UX and accepted reconciliation are missing.
- **Dependencies and flag:** requires Offline integrity, returns, split bills and stored-
  value boundaries; add `enable_loyalty_ui`, dependent on a valid company/profile Loyalty
  Program and accounting configuration.
- **Accounting/reversal invariants:** points earned/redeemed/expired equal ERPNext loyalty
  entries; redemption discount/value and any configured liability/expense reconcile with
  invoice and GL; returns/cancellations create standard compensating entries; never mix
  loyalty points with stored-value gift-card liability.
- **Security/idempotency/concurrency:** customer/profile/company scope; server calculates
  eligibility and balance at submit; lock/recheck concurrent redemption; durable invoice
  keys prevent duplicate earn/redeem; manual adjustments require manager permission and
  audit; offline redemption is denied unless a later explicit safe policy exists.
- **Arabic/English UX:** active-locale balance, earn/redeem estimate, tiers, expiry and
  failure reasons; RTL/LTR, touch and receipt clarity without marketing unsupported value.
- **Acceptance:** program validation tests; earn/redeem/partial/return/cancel/expire and
  concurrent redemption tests; real ERPNext loyalty-entry/invoice/GL reconciliation;
  direct API/flag/user-permission negatives and manual bilingual customer journey.
- **Definition of Done:** an actual QA program is configured and reconciled, no double
  points or cross-company leakage, flag restored off, tests/docs/build/commit complete.
- **External decision/blocker:** business/accounting must choose earning rules, tiers,
  expiry, redemption value/accounts and offline policy; current absence of an active
  program is a product blocker, not proof of capability.

### Milestone 10 — Quick restock

- **Business outcome:** managers turn defensible low-stock signals into standard Material
  Requests/Purchase Orders without creating a parallel buying system or excess duplicates.
- **Baseline versus missing:** the completed Milestone 2 Item/Supplier/Purchase workflow,
  warehouses, prices and stock ledgers are mandatory reusable foundations; alerts,
  reorder suggestions, supplier selection, document conversion and forecasting are absent.
- **Dependencies and flag:** depends explicitly on accepted purchases `8b5145d` plus
  correction `8f4a067`, catalog performance, supplier permissions and stock history; add
  `enable_quick_restock`, dependent on `enable_purchases`.
- **Accounting/stock risks:** suggestions post nothing; only standard ERPNext Material
  Request/Purchase Order/Purchase Receipt/Purchase Invoice controllers affect commitments,
  stock or GL. Respect company/warehouse/UOM/lead time, open supply, reserved stock,
  returns/cancellations and multi-currency buying prices.
- **Security/idempotency/concurrency:** manager-only company/profile scope; server recomputes
  shortage before create; deterministic suggestion/run key; lock or atomic check against
  open requests/orders; prevent duplicate/excess restock; preserve document lineage and
  standard cancellation permissions.
- **Arabic/English UX:** localized low/out/slow-moving reasons, projected stockout date,
  editable recommendation with assumptions, supplier/warehouse selection, RTL/LTR,
  responsive confirmation and history.
- **Acceptance:** calculation tests for demand windows, open supply and edge stock;
  permission/flag/API negatives; duplicate/concurrent generation; standard document
  submit/cancel and stock reconciliation; manual no-stock/slow-moving/multi-warehouse flow.
- **Definition of Done:** every generated document is standard ERPNext and traceable,
  duplicate/excess protection proven, forecasts labelled as estimates, flag off, tests/
  docs/build/commit complete.
- **External decision/blocker:** product/operations must approve demand horizon, safety
  stock, lead-time source and whether Purchase Order conversion is automatic or reviewed.

### Milestone 11 — Payment integrations and ZATCA/compliance

- **Business outcome:** optional external payments settle and refund reliably, while
  Saudi e-invoicing is represented truthfully and activated only with verified compliance.
- **Baseline versus missing:** reuse POS payments, Payment Entry/invoice idempotency,
  printing and current Phase 1 QR assistance. No provider adapter/credentials/webhook/
  settlement reconciliation exists; QR support is not ZATCA Phase 2 clearance/reporting.
- **Dependencies and flags:** requires Offline integrity and stable payment/return flows.
  Add company flags `enable_payment_integrations` and `enable_zatca_phase2`; activation
  requires configured provider or validated compliance profile respectively.
- **Accounting/reversal invariants:** provider intent is not revenue or settlement;
  authorized/captured/settled/refunded/charged-back amounts reconcile by currency with
  Sales Invoice, payment/clearing/bank GL and provider statements; retries never double
  capture/refund; cancellation uses compensating provider and ERPNext records. ZATCA
  submission never changes invoice totals and stores immutable UUID/hash/status/response
  lineage for original and cancellation/credit notes.
- **Security/idempotency/concurrency:** secrets outside code/logs, least-privilege access,
  signed webhook verification with timestamp/replay protection, durable provider event and
  operation keys, atomic state machine, out-of-order event handling, settlement locks,
  certificate/key lifecycle, audited overrides, and direct API flag/permission negatives.
- **Offline risks:** provider payments fail closed offline unless the chosen provider has
  an explicitly certified terminal protocol; queue ZATCA reporting only under the agreed
  compliance mode with bounded retry, ordering, expiry/escalation and recovery evidence.
- **Arabic/English UX:** localized provider/status/retry/refund/reconciliation states and
  compliance receipt/status messages, RTL/LTR, no raw gateway or certificate errors.
- **Acceptance:** provider contract/sandbox tests, signed/invalid/duplicate/out-of-order
  webhooks, timeout/retry/refund/chargeback and settlement reconciliation; ZATCA official
  sandbox XML/signature/clearance-or-reporting tests, certificate rotation and credit-note
  linkage; manual bilingual cashier/finance recovery; security review and build gates.
- **Definition of Done:** one explicitly selected provider and/or compliance profile passes
  sandbox-to-ledger reconciliation, secrets are managed, reversal/recovery is proven,
  flags remain off until release approval, documentation and focused commits complete.
- **External decision/blocker:** provider selection and credentials, settlement accounts,
  ZATCA compliance profile, certificate lifecycle owner and test credentials are required
  external decisions. Never guess or claim Phase 2 from QR output.

### Milestone 12 — Separate restaurant/KDS/native/customer-display/advanced-analytics initiatives

- **Business outcome:** separately specified products can extend the accepted retail POS
  without destabilizing its sale, accounting, offline or security contracts.
- **Baseline versus missing:** retail POS components, realtime infrastructure, reports and
  responsive web UI may be reused after audit. Table service, order routing/merge/KDS,
  native apps, secure customer display, connector lifecycle and advanced forecasting/
  targets are not existing accepted products.
- **Dependencies and flags:** begin only after Milestones 3–11 review. Restaurant uses
  `enable_restaurant_mode`; customer display uses `enable_customer_display`; analytics
  uses company `enable_advanced_analytics`. Native and KDS flags/scope must come from their
  approved specifications, not be invented in implementation.
- **Accounting/offline/data risks:** restaurant transfers/splits/voids must preserve order-
  to-invoice lineage and reversal; KDS acknowledgements must not post accounting; native
  offline storage must match server idempotency/conflict policy; customer display must
  expose only the active sanitized basket; analytics must be read-only, source-defined,
  timezone-correct and never present forecasts as booked results.
- **Security/idempotency/concurrency:** authenticated per-device channels, tenant/profile/
  company isolation, revocable pairing, no PII/payment token leakage, ordered event IDs,
  reconnect deduplication, concurrent table/order ownership rules, native secure storage,
  and auditable manager overrides.
- **Arabic/English UX:** each initiative requires its own responsive/touch/accessibility
  design, active-locale Arabic/English and verified RTL/LTR; KDS and customer display need
  role/device-appropriate minimal views rather than copying manager screens.
- **Acceptance:** separate PRD/threat/accounting/offline design first; then unit/Frappe/
  frontend/device/E2E/performance/security tests and manual multi-device bilingual flows.
  Restaurant acceptance includes transfer/merge/void/print/KDS recovery; customer display
  includes pairing/revocation/data-leak tests; analytics reconciles every metric to sources.
- **Definition of Done:** each initiative is approved and delivered as its own milestone/
  program with secure-off activation, complete acceptance evidence and local review; none
  is bundled into a broad retail rewrite.
- **External decision/blocker:** restaurant operating behavior, KDS/printer topology,
  native platform/offline/release scope, customer-display pairing/security policy,
  connector ownership and advanced-analytics KPI definitions are all external decisions.

## Cross-Cutting Technical Debt and Product Blockers

### Non-blocking technical debt

- **ERPNext Standard Buying test-bootstrap history:** earlier selected `bench run-tests`
  attempts failed before module loading because ERPNext tried to create a duplicate
  `Standard Buying` Price List. Milestone 2 selected Frappe suites later passed normally
  (14/16/10) without deleting data. Treat this as historical/intermittent harness debt:
  preserve the non-destructive runners, record exact recurrence evidence, and never delete
  user data to make bootstrap pass. It is not currently a product blocker.
- **Historical report settlement anomaly:** the read-only `الجوالات` dataset reconciled
  signed tender to ERPNext paid amount, but the invoice-balance equation retained a
  visible `1,050.00` difference traced to three historical invoices whose negative
  outstanding changed after original POS tender. Do not rewrite history or claim it is
  resolved; keep the discrepancy visible and exclude it from unrelated milestone claims.
- **Development build warnings:** Vite succeeds but retains deployment-time Digit/demo
  asset/font references, third-party pure-annotation warnings, and mixed static/dynamic
  import warnings. Node 18 currently needs
  `NODE_OPTIONS=--experimental-global-webcrypto`. These are non-blocking until a scoped
  asset/chunk/runtime modernization task is approved.
- **Legacy formatting/tooling:** broad Biome checks may surface unrelated legacy Vue
  formatting/parser findings. Continue targeted checks plus actual Vite compilation;
  do not mix mass reformatting into financial/offline milestones.

### Product/external blockers

- Credit thresholds/re-auth/offline policy; stored-value liability/expiry/refund policy;
  loyalty earning/redemption/accounting rules; performance budgets/devices; and restock
  forecasting/review policy require owner decisions at their named milestones.
- Payment provider/credentials/settlement accounts and ZATCA compliance profile/test
  credentials are hard blockers for Milestone 11 activation.
- Restaurant behavior, KDS topology, native scope, customer-display security/pairing,
  connector ownership and advanced-analytics KPI definitions are hard blockers for their
  separate Milestone 12 initiatives.
- A blocked external sub-scope does not block safe independent milestones; document it,
  keep its flag unavailable/off, and continue only work that does not assume the decision.

## Next Session Command

Start with the first incomplete ledger item: **Milestone 3 — Offline end-to-end
integrity**. Work only in `/home/erpnext/frappe-bench16/apps/posnext` on existing branch
`develop`; do not create a branch. Re-read this file and
[`DEVELOPMENT_MASTER_PLAN.md`](DEVELOPMENT_MASTER_PLAN.md), verify the checkout/commit and
preserve user changes, then perform a fresh code-and-test audit before editing. Keep every
new or changed rollout flag secure-off by default. Do not edit, build, migrate, restart,
switch or deploy `/home/erpnext/frappe-bench-startd-prod` or `pos.digit-erp.com`. Make
focused local commits only; no push, merge or deployment. Complete and document Milestone
3 acceptance, leave flags off and the worktree clean, then stop for review before
Milestone 4.

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
- Removed `POS Cashier` write permission from `POS Settings`. The generic settings
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

## 2026-08-21 — Workspace ownership cleanup and framework update

- Updated the local `version-16` branches by merging the current official releases:
  Frappe `16.31.0` and ERPNext `16.32.3`. Both merges completed without conflicts.
- Built Frappe and ERPNext assets, migrated `pos.yemenfrappe.com`, cleared cache, and
  restarted web, socketio, scheduler, and worker services.
- Removed only the legacy `Tools` workspace because it had no application ownership;
  its matching `Desktop Icon` and `Workspace Sidebar` were also removed. The cleanup is
  recorded as `pos_next.patches.v2_1_0.remove_unowned_tools_workspace`.
- Kept standard Frappe/ERPNext workspaces untouched, including `Accounting`, whose
  Desktop Icon is explicitly owned by ERPNext. App-owned workspaces retained: `POS`
  (`pos_next`) and `WhatsApp` (`frappe_conversations`).
- Pre-update uncommitted work in Frappe and ERPNext was preserved safely in named Git
  stashes (`codex-pre-update-20260821-*`) and intentionally not reapplied automatically.

### Follow-up correction

- Compared workspaces to `upstream/version-16` rather than the locally merged trees.
  Five legacy local customizations were correctly identified and removed from the site:
  `Accounting.`, `Custom Users`, `Financial Management`, `Reports`, and
  `Customization`. Their Workspace Sidebar and Desktop Icon records were removed too.
  The cleanup is recorded as
  `pos_next.patches.v2_1_0.remove_legacy_custom_workspaces`.

- Final navigation audit also removed legacy `ERPNext Integrations` Workspace,
  `Selling.` Sidebar, and orphaned `Payables`/`Receivables` Desktop Icons. The old
  source files for the five removed workspaces were deleted after migration (workspace
  sync runs before patches). Effective source comparison to `upstream/version-16` and
  site-record checks are clean. Patch:
  `pos_next.patches.v2_1_0.remove_all_legacy_workspace_navigation`.

## 2026-08-21 — Forced upstream replacement

- At the user's explicit request, force-reset `apps/frappe` and `apps/erpnext` to
  `upstream/version-16`, removing all local commits and working-tree customizations.
  Final source trees exactly match Frappe `16.31.0` (`6a329d0684`) and ERPNext
  `16.32.3` (`11e0ba0a1c`).
- Reinstalled requirements, rebuilt assets, migrated `pos.yemenfrappe.com`, cleared
  cache, and restarted services. Existing pre-reset stashes remain preserved but are
  not applied.

## 2026-08-21 — Static asset and Leany integration health

- Fixed public-asset permissions after the forced reset: 462 files below application
  `public/` folders lacked world-read permission, which made Nginx return 404 for the
  ERPNext `Organization` icon. All public files are now readable; the icon and sampled
  Frappe, ERPNext, POS Next, and Universal Standard assets return HTTP 200.
- Audited `leany-frappe` upstream. It is a Desk CSS-only design system; its existing
  Universal Standard integration is injected after the main Universal CSS for every
  `/app` response. Added the previously missing native Leany dark-mode token palette
  and versioned the asset URL as `20260821_leany_complete` for cache invalidation.
- Verified Python compilation, diff whitespace, asset delivery, `/api/method/ping`, and
  two active workers via `bench --site pos.yemenfrappe.com doctor`.

### Desk route correction

- The site serves its authenticated Desk at `/desk`, while Universal Standard had been
  injecting its UI/Leany assets only for `/app`. Updated the injector to support both
  routes and bumped the asset version to `20260821_leany_desk`; cache cleared and
  services restarted. Guest HTTP checks redirect before Desk HTML is rendered, while
  the authenticated `/desk` response now meets the injector's route condition.

## 2026-08-22 — POS catalogue and purchase workflow verification

- Confirmed every enabled POS Settings profile enables both catalogue management and
  purchases. Catalogue management already exposes the functional add-item action.
- Added a visible "Add Supplier" action in the purchase-invoice form, using the
  existing permission-checked supplier quick-create API (name, mobile number and
  supplier group are required).
- Added a permission-scoped Excel/CSV purchase-invoice importer. It accepts Arabic or
  English headers, validates uploaded-file ownership, item purchasing eligibility,
  quantity and rate, and only pre-fills a draft form; it cannot save or submit a
  financial document. Required columns: Item Code or Item Name, Quantity, Purchase
  Rate; Unit is optional.
- Built the POS frontend, passed `PurchaseInvoiceForm` tests (5/5), verified Python
  compilation and the import-header parser, cleared cache, and restored the managed
  Frappe services after discovering the local Supervisor socket/services were down.

## 2026-08-23 — Durable multi-company POS isolation

- Added idempotent company provisioning for item, customer and supplier groups plus a
  walk-in customer and default supplier. Every record is bound to the company through
  `custom_pos_company`; group display names are derived from the company but ownership
  is enforced by the relationship, not by text matching.
- Provisioning runs for the initial Company at app installation, after every migration,
  whenever multi-company mode is enabled, and after creating a new Company.
- Added the `POS User Company` child DocType and the User field `POS Allowed Companies`.
  The ordered list is now the source of truth: its first company is the User/POS default
  and the app synchronizes native Company User Permissions, removing obsolete company
  grants to prevent stale access.
- Migrated existing users without guessing access: their legacy default or existing
  Company User Permissions were adopted into the new selector. Users without either
  remain fail-closed until an administrator assigns a company.
- Verified migration, default master branches for all current companies, a Phones user
  permission round-trip, Python/JSON/diff checks, POS frontend build, cache clear and
  web-service restart. Production unit tests remain disabled by site configuration.
