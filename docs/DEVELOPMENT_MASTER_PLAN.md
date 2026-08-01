# Digit POS — Master Development and Delivery Plan

This plan converts the verified capability gaps into a controlled development
program. It favors correctness, accounting integrity, and incremental activation over
large simultaneous rewrites.

## Delivery Model

- One development branch: `develop`.
- One protected production branch: `digitpos`, unchanged until explicit approval.
- Work in milestones on the same branch; make a focused commit after each accepted
  milestone.
- Use independent feature flags to keep unfinished capabilities inaccessible.
- Finish and verify one vertical slice before starting a dependent slice.

## Feature Flag Foundation — Milestone 0

Replace `ENABLE_NEW_MANAGEMENT_FEATURES` with persisted, independently controlled
settings. Prefer fields on POS Settings for profile-scoped behavior and a dedicated
single settings DocType only for site-wide experimental modules.

Initial flags:

| Flag | Default | Scope | Purpose/dependency |
|---|---:|---|---|
| `enable_catalog_management` | Off | POS Profile | Item/group/price management |
| `enable_purchases` | Off | POS Profile | Purchase invoice workflow |
| `enable_supplier_payments` | Off | POS Profile | Requires purchases |
| `enable_pos_reports` | Off | POS Profile | In-POS dashboard for permitted managers |
| `enable_keyboard_shortcuts` | Off | POS Profile | Global POS shortcuts |
| `enable_credit_approval` | Off | POS Profile | Requires credit sales |
| `enable_split_bills` | Off | POS Profile | Split-cart workflow |
| `enable_stored_value_gift_cards` | Off | Company | Ledger-based gift cards |
| `enable_loyalty_ui` | Off | POS Profile | Requires configured Loyalty Program |
| `enable_quick_restock` | Off | POS Profile | Requires purchases |
| `enable_advanced_analytics` | Off | Company | Enhanced analytics/forecasting |
| `enable_restaurant_mode` | Off | POS Profile | Separate restaurant workflow |
| `enable_customer_display` | Off | POS Profile | Customer-facing second screen |
| `enable_payment_integrations` | Off | Company | Requires configured provider |
| `enable_zatca_phase2` | Off | Company | Requires certificates and compliance setup |

Feature-flag requirements:

- Manager-only settings UI with clear Arabic and English description, risk, and
  dependencies for each flag.
- Backend helper such as `require_feature(feature, pos_profile=None, company=None)`.
- Backend endpoints must reject disabled features even if invoked directly.
- Audit changes to flags with user, timestamp, old value, and new value.
- Validate dependencies and prevent unsafe activation.
- Bootstrap flags once per session and invalidate them through realtime/cache events.
- Tests for defaults, permissions, dependency checks, and direct API bypass attempts.

## Milestone 1 — Reports and Operational Insight (P0)

### Scope

1. Fix ERPNext 16 report schema compatibility (`posting_date` + `posting_time` or a
   supported computed datetime; never query nonexistent fields).
2. Establish the authoritative sales doctype and consistent return/sign conventions.
3. Enforce user access to POS Profiles, companies, and permitted documents.
4. Enable the in-POS report dashboard only for authorized managers through
   `enable_pos_reports`.
5. Provide safe links or embedded access to the five existing Desk reports.
6. Add export/print where the current context supports it.
7. Cover sales, net sales, invoice count/average, returns, outstanding credit,
   payments, recent transactions, shifts, cash variance, and taxes.
8. Add seeded development acceptance data for cash/card/partial/credit/return cases.

### Acceptance

- Totals reconcile with ERPNext queries for the same filters.
- Returns are signed and counted correctly.
- Cashiers cannot access manager reports or foreign profiles through UI or API.
- Date boundaries respect site timezone.
- All five existing reports execute without regression.
- New dashboard tests pass on ERPNext/Frappe 16.

## Milestone 2 — Catalog, Purchases, and Supplier Payments (P0)

### Scope

- Audit and harden the existing hidden catalog, purchase, and supplier-payment code.
- Complete item/group creation, selling and buying prices, suppliers, purchase invoice
  draft/submit/cancel, Payment Entry draft/submit/cancel, outstanding balances, and
  payment history.
- Enforce company, account, warehouse, price-list, and document permissions.
- Validate accounting entries and stock ledger effects against ERPNext.
- Provide independent flags and dependency rules.

### Acceptance

- No operation uses a company, warehouse, account, or supplier outside user access.
- Submitted/cancelled documents reconcile with ERPNext ledgers.
- Duplicate supplier payments are prevented.
- Cashier cannot access these capabilities; manager access is explicit.

## Milestone 3 — Offline Integrity (P0)

### Scope

- Execute real offline sales, multiple queued invoices, reconnection, retry, and
  deduplication scenarios.
- Add an operator-visible failed/pending/conflict queue and recovery actions.
- Define conflict policy for changed price, stock, customer, shift, payment mode, and
  expired promotions.
- Preserve printed-before-sync warnings and idempotency identifiers.
- Add health metrics and populate Offline Invoice Sync evidence.

### Acceptance

- Repeated retry never creates duplicate invoices or payments.
- A closed/changed shift has a documented and safe reconciliation path.
- Every failure is actionable and retains audit evidence.
- Online and offline totals match for the same transaction inputs.

## Milestone 4 — Keyboard Productivity (P1)

- F4 item search, F8 customer search, F9 checkout, Ctrl/Cmd+S draft, and consistent
  Escape handling.
- Ignore global shortcuts while editing text or when an incompatible modal owns focus.
- Add an accessible shortcut-help overlay and automated event tests.

## Milestone 5 — Credit Approval (P1)

- Customer credit limit, payment-term policy, overdue exposure, configurable exception
  thresholds, manager PIN/re-auth approval, approve/reject trail, and reporting.
- Backend must re-evaluate policy at submission time to prevent UI bypass.
- Returns and cancellations must reverse exposure correctly.

## Milestone 6 — Split Bills (P1)

- Split by items, quantities, equal values, or custom values.
- Maintain a parent split session and child invoice lineage.
- Preserve proportional discounts, taxes, free items, payment allocation, returns,
  printing, shift attribution, and offline idempotency.
- Never use rounding adjustments to hide an allocation mismatch.

## Milestone 7 — Stored-Value Gift Cards (P1)

- Create a dedicated card and immutable transaction ledger.
- Issue, activate, top up, redeem partially, refund, freeze, expire, and cancel.
- Add barcode/code security, concurrency locking, idempotency, accounting liability,
  and complete audit history.
- Keep existing promotional Gift Card coupons separate and label them accurately.

## Milestone 8 — Large-Catalog Performance (P1)

- Implement real windowed/virtual rendering rather than configuration-only thresholds.
- Benchmark 10k and 50k item datasets on desktop and constrained tablet profiles.
- Preserve keyboard focus, grid/list modes, lazy images, barcode search, and RTL.
- Define budgets for initial render, search latency, memory, and scroll smoothness.

## Milestone 9 — Loyalty (P2)

- Configure ERPNext Loyalty Program per company/profile.
- Earn, redeem, reverse, expire, and audit points.
- Add tier visibility and wallet liability reconciliation.
- Do not activate UI until an actual program and accounting configuration pass
  validation.

## Milestone 10 — Quick Restock (P2)

- Low/out-of-stock alerts, reorder policy, velocity-based suggestions, supplier choice,
  Material Request generation, Purchase Order conversion, duplicate/excess protection,
  slow-moving inventory insight, and forecasted stockout date.
- Build on the accepted purchase workflow; do not implement a parallel purchasing path.

## Milestone 11 — Integrations and Compliance (P2/P3)

### Payment providers

- Provider adapter interface, intent creation, signed webhook verification, idempotency,
  settlement, refund, failure recovery, and reconciliation reports.
- Provider selection and credentials are external decisions and must not be guessed.

### ZATCA Phase 2

- Treat current QR support as Phase 1 assistance only.
- Add standards-based XML, cryptographic signing, certificate lifecycle, clearance or
  reporting flow, response storage, retry, UUID/status, audit, and compliance tests.
- Require an agreed compliance profile and test credentials before activation.

## Milestone 12 — Separate Product Initiatives (P3)

These require their own specifications after the retail POS program is stable:

- Restaurant/table/order transfer/merge/KDS/kitchen printing.
- Native iOS and Android application.
- Customer-facing display and secure realtime channel.
- Integration Hub and connector lifecycle.
- Forecasting, targets, branch comparison, and executive analytics.

## Testing Strategy

For every milestone, select and run the applicable layers:

1. Python unit tests for calculation and policy functions.
2. Frappe integration tests for documents, permissions, ledgers, and hooks.
3. Frontend component/store tests for state and interaction.
4. Browser E2E for the complete cashier/manager journey.
5. API-negative tests for disabled flags and insufficient roles.
6. Arabic/English and RTL/LTR visual/interaction checks.
7. Offline/reconnect/conflict tests for transaction features.
8. Build and static checks (`git diff --check`, frontend build, relevant linters).
9. Performance tests for catalog/report-heavy changes.

## Milestone Execution Loop

For each milestone:

1. Re-audit existing code and tests; reuse proven implementation.
2. Write a short technical design and data/accounting effects.
3. Add or update the feature flag and backend enforcement.
4. Write failing tests for the critical rules.
5. Implement the smallest complete vertical slice.
6. Run focused tests, then regression tests.
7. Build frontend assets only in the development bench.
8. Perform the documented manual acceptance scenario on the development site.
9. Update `PROJECT_MEMORY.md` and user-facing documentation.
10. Create a focused local commit on `develop`.
11. Stop before push, merge, or production deployment unless explicitly authorized.

## Priority Order

1. Feature flag foundation.
2. Reports.
3. Catalog/purchases/supplier payments.
4. Offline integrity.
5. Keyboard productivity.
6. Credit approval.
7. Split bills.
8. Stored-value gift cards.
9. Large-catalog performance.
10. Loyalty.
11. Quick restock.
12. Integrations and ZATCA.
13. Separate restaurant/native/customer-display/forecasting programs.

