# Digit POS Development Program — Project Memory

Last verified: 2026-08-01

This file is the durable memory and source of operational context for the Digit POS
development program. Read it before changing code, and update the progress section
after every completed milestone.

## Non-Negotiable Environment Boundary

| Environment | Site | Checkout | Branch | Verified commit | Policy |
|---|---|---|---|---|---|
| Production | `pos.digit-erp.com` | `/home/erpnext/frappe-bench-startd-prod/apps/posnext` | `digitpos` | `49c70f5` | Keep unchanged until an explicit, approved release |
| Development | `digitpos.trilogy-erp.com` | `/home/erpnext/frappe-bench16/apps/posnext` | `develop` | based on `a182d9e` | All new work happens here |

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

The in-POS dashboard added in commit `9573cef` is different from those reports. It is
currently hidden and has an ERPNext 16 compatibility defect: `pos_next/api/reports.py`
queries the nonexistent Sales Invoice field `posting_datetime`. It must be corrected
and covered by tests before it is enabled.

## Existing Hidden Management Modules

The following implementations exist but are intentionally hidden by
`ENABLE_NEW_MANAGEMENT_FEATURES = false` in `POS/src/pages/POSSale.vue`:

- Catalog and item management.
- Purchase invoices.
- Supplier payments.
- In-POS report dashboard.

Replace the hard-coded umbrella constant with independent server-controlled feature
flags. A hidden UI element is not a security boundary; backend permission and feature
checks are mandatory.

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
| Feature flag foundation | Not started | — | First implementation milestone |
| Reports compatibility and in-POS access | Not started | — | First product feature milestone |
| Catalog/purchases/supplier payments hardening | Not started | — | Existing hidden code |
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
