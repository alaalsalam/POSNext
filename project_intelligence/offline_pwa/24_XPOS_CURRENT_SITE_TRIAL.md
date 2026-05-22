# XPOS Current Site Trial

## Summary
Decision: `INSTALL_BLOCKED_BY_COMPATIBILITY`

## Why we stopped before install
The current site is not a neutral sandbox. It already contains a client-demo-ready POSNext deployment with working `/pos`, PWA, offline sync, accounting baseline, and validated demo users.

XPOS `version-15` is not just an extra route. Its hooks modify core ERPNext/POS behavior:
- `doctype_js` for `POS Profile`, `Sales Invoice`, `Company`
- `extend_bootinfo`
- `override_doctype_class` for `POS Invoice`
- `doc_events` for `Sales Invoice`, `POS Invoice`, `Customer`

Given the user's stop conditions, this is enough to block installation on the live demo site.

## Environment gate
Current server:
- Frappe `15.107.2`
- ERPNext `15.107.0`
- Python `3.10.12`
- Node `12.22.9`

XPOS version-15 requires:
- Frappe `v15`
- ERPNext `v15`
- Python `>= 3.10`
- Node `>= 18`

So the framework line is acceptable, but Node is below minimum and the hook surface is unsafe for side-by-side current-site installation.

## Outcome
- POSNext uninstalled: `No`
- XPOS fetched into current bench: `No`
- XPOS installed on current site: `No`
- migrate: `No`
- build: `No`
- `/pos` preserved: `Yes`

## Recommendation
Continue with lab-only validation in an isolated bench/site if XPOS still matters. Do not move to replacement planning on `pos.yemenfrappe.com` from this trial result.
