# Upstream `develop` Review — 2026-07-29

This review records how Digit POS consumes improvements from the official POSNext
repository without replacing the customized `digitpos` branch.

## Repositories and Policy

- Digit POS source of truth: `github` → `alaalsalam/POSNext`, branch `digitpos`.
- Official read-only reference: `upstream` → `BrainWise-DEV/POSNext`, branch `develop`.
- Official reference reviewed: `a051da9`.
- Common ancestor reviewed: `0b8b6f3`.

Never merge `upstream/develop` wholesale into `digitpos`. Review upstream commits and
port only changes that are compatible with Digit branding, permissions, offline
behavior, Frappe/ERPNext versions, and current business workflows.

## Difference Summary

At review time:

- `digitpos` had 36 unique commits after the common ancestor.
- `upstream/develop` had 6 unique commits after the common ancestor.
- The upstream changes covered Min/Max promotional discounts, the `1.17.0` frontend
  version, mandatory customer mobile numbers, and an `All Item Groups` eligibility fix.

## Adopted

### `All Item Groups` offer eligibility

Source upstream commit: `cbc746f`.

Digit POS now treats `All Item Groups` as every cart item in:

- Offline offer application in `POS/src/stores/posCart.js`.
- Eligible quantity calculation in `POS/src/stores/posOffers.js`.
- Offer eligibility checks in `POS/src/stores/posOffers.js`.

This is a contained correctness fix and does not change offer behavior for explicitly
selected item groups.

### Frontend version `1.17.0`

Source upstream commit: `44119bc`.

`POS/package.json` now matches the Frappe app version. This removes the misleading
`v1.16.0` label from a deployment whose backend is already `1.17.0`.

## Adopted After Product Approval

### Mandatory customer mobile number

Source upstream commit: `56ddf7a`.

Adopted after explicit product approval. The Digit customer dialog keeps its customized
layout and country selector, but now marks the mobile number as required, disables the
save action while it is empty, and validates it before creating or updating a customer.

### Min/Max discount engine

Source upstream commits: `cbc746f`, `5364a7e`.

Adopted after explicit product approval. The implementation:

- Monkey-patches ERPNext pricing functions during package import.
- Adds validation hooks to Sales Invoice, Sales Order, Quotation, Delivery Note, and
  POS Invoice.
- Adds custom fields and cross-item discount recalculation.
- Supports cheapest (`Min`) and most-expensive (`Max`) item ranking with a configurable
  discounted quantity limit.

Because this changes core pricing behavior, future ERPNext upgrades must retest the
override against the exact installed version.

## Future Review Command

```bash
cd /home/erpnext/frappe-bench16/apps/posnext
git fetch upstream develop
git log --oneline digitpos..upstream/develop
git diff --stat digitpos...upstream/develop
```

Always apply selected changes on `digitpos`, run the normal build and backend
verification, and create a Digit-owned commit describing the upstream source.
