# Readiness

## Current State
- Adopted into BildFast as an existing Frappe app.
- Project: LP-00022.
- Site: pos.yemenfrappe.com.
- Route: /desk.

## Known Constraint
Most existing public sites send `X-Frame-Options: SAMEORIGIN`; iframe preview in `lovable.yemenfrappe.com` may require a controlled header/CSP adjustment per site.
