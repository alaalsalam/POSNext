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

## Not Adopted

### Mandatory customer mobile number

Source upstream commit: `56ddf7a`.

Not adopted because requiring a phone number is a business policy, not a universal bug
fix. Digit POS targets fast cashier workflows and small merchants; customer creation
must remain possible without inventing contact data. If required later, implement it
as a POS Profile setting rather than a global hard requirement.

### Min/Max discount engine

Source upstream commits: `cbc746f`, `5364a7e`.

Not adopted in this production pass. The implementation:

- Monkey-patches ERPNext pricing functions during package import.
- Adds validation hooks to Sales Invoice, Sales Order, Quotation, Delivery Note, and
  POS Invoice.
- Adds custom fields and cross-item discount recalculation.
- Did not include focused automated tests in the upstream commits.

This is a useful feature candidate, but it requires isolated tests against the exact
Frappe/ERPNext 16 versions before it can safely enter Digit POS.

## Future Review Command

```bash
cd /home/erpnext/frappe-bench16/apps/posnext
git fetch upstream develop
git log --oneline digitpos..upstream/develop
git diff --stat digitpos...upstream/develop
```

Always apply selected changes on `digitpos`, run the normal build and backend
verification, and create a Digit-owned commit describing the upstream source.
