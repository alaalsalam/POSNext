<!-- bildfast:plan id=0020 status=approved agent=bildfast task="Make the app's permissions fully app-owned and self-documenting (not dependent on ad-hoc ERPNext role setup)" -->
# Plan: App-owned, self-documenting permission model

## Overview
User wants the app's permissions to be **complete and owned by the app** — clear and
understandable from their names, working on any install without manual permission setup or
review, and not silently dependent on ERPNext's own roles/permissions.

## What's actually the gap (diagnosed this session, not assumed)
The role *names* are already fine and self-documenting (`POSNext Cashier`, `POS Manager`) and
are referenced by code (`FEATURE_MANAGER_ROLES`, `REPORT_MANAGER_ROLES`), the 5 report JSONs,
and 21+ live `Has Role` rows. **Renaming them is high-risk, zero-value — out of scope.**

The real gap: the grants those roles rely on are **unshipped site data**. Specifically, the
DocPerms that make POS Manager / POSNext Cashier actually work on core doctypes (Item, Sales
Invoice, Purchase Invoice, Payment Entry, Promotional Scheme, POS Coupon, POS Settings, POS
Closing Shift, Customer, Company, Warehouse …) currently exist as **runtime `Custom DocPerm`
records on this site**, not in the app. That's exactly why it "works here but would break on a
fresh install / needs manual review." Several fixes this session (Company-read wall, report role
records, feature flags) were also site-data patches, not shipped config.

## Plan (to be executed on approval — @bildfast-backend)
1. **Author the full DocPerm matrix in the app**, using the mechanism the app already uses:
   the `custom/<doctype>.json` fixtures' `custom_perms` array (our `custom/user.json` already
   has the empty key). One file per core doctype the POS touches, each granting the exact rights
   for **both** tiers:
   - **POSNext Cashier** (base): sell — read/create/submit Sales Invoice, read Item/Customer/etc.,
     read-only on Promotional Scheme / POS Coupon (deliberately NOT create/write — must stay
     read-only), read POS Settings, etc.
   - **POS Manager** (adds on top): create/write Item; create/write/delete Promotional Scheme &
     POS Coupon; write POS Settings; create/write/submit/cancel Purchase Invoice & Payment Entry;
     read POS Closing Shift; Company/Warehouse read; etc.
   The matrix is not invented — it is exactly what `get_pos_permissions` already encodes, so the
   fixtures reproduce the existing contract rather than widening it.
2. **Sync on migrate** (these fixtures apply automatically), and apply to THIS live site via the
   same targeted-insert pattern used all session (since I can't run `bench migrate`).
3. **Keep the app-role checks as the single source of truth.** The API guards already key off
   `POS Manager` / `POSNext Cashier` / the role-sets; no dependence on ERPNext manager roles is
   introduced. Where an API still leans on an ERPNext role, switch it to the app role.
4. **Ship the 5 report role records + the Company/warehouse defaults** properly too, so the
   report-access and Company-read fixes from this session are in code, not just live data.

## Proof of "doesn't depend on ERPNext permissions" (acceptance test)
- Create two throwaway users: one with **only** `POSNext Cashier`, one with **only**
  `POSNext Cashier + POS Manager` — and **no** ERPNext roles (no Sales User / Stock User /
  Accounts User). Run the existing `get_pos_permissions` + report-access audit scripts against
  both.
- **Pass = ** cashier can sell + read (but not manage promotions/settings/catalog), manager gets
  the full set — with zero ERPNext roles attached. Only after that passes (and you approve) would
  we consider stripping the extra ERPNext roles from the live demo users.
- FrappeTestCase coverage: a test that asserts the two tiers' capabilities from the shipped
  fixtures (so it can't silently regress).

## Guardrails
- Two tiers preserved exactly — a "complete permissions" pass must NOT widen cashier access.
- No role renames. No `ignore_permissions` shortcuts.
- Reversible: fixtures + targeted inserts; the live demo users' current ERPNext roles are left in
  place until the acceptance test proves the app-only path works.

## Execution Note
Implemented — but the mechanism had to change from the plan's "custom_perms fixtures" after a
safety check, because that mechanism is destructive here:

- **Why not custom_perms fixtures:** Frappe's `sync_customizations_for_doctype` **deletes ALL
  Custom DocPerm for a doctype and recreates them from the file** on migrate. These core
  doctypes already carry Custom DocPerm for many ERPNext roles (Item = 11 roles, Customer = 10,
  Sales Invoice = 7, …). Shipping a `custom_perms` with only the 2 POS roles would have **wiped
  every other role's access** on migrate. Also, adding any Custom DocPerm to a doctype that
  currently uses standard perms disables all standard perms. So fixtures were the wrong tool.
- **What I shipped instead:** `pos_next/patches/v2_0_0/ship_pos_role_permissions.py` (registered
  in `patches.txt`), which applies the exact matrix via `frappe.permissions.add_permission` +
  `update_permission_property`. `add_permission` first snapshots a doctype's standard perms into
  Custom DocPerm (preserving every existing role) before adding a POS role, so it is
  **non-destructive and idempotent** — and works identically on a fresh install (which starts
  from standard perms) and here.
- **Matrix source:** extracted the live Custom DocPerm for both roles across the 12 core
  doctypes and embedded it verbatim — reproduces the existing contract, does not invent or widen
  it. App-owned doctypes (POS Coupon, POS Settings, POS Opening/Closing Shift, POS Offer,
  Referral Code) already ship their perms in their doctype JSON; untouched.

**Applied live + verified (this site):**
- Ran the patch: **no other role lost any perm** (before/after diff across all roles on the 12
  doctypes), and the POS roles' grants are unchanged (idempotent).
- **Acceptance proof** (`pos_next/tests/test_role_permissions.py`, run green): two users with
  **only** the app roles and **zero** ERPNext roles (no Sales User / Stock User / Accounts User)
  — cashier can sell / take payments / create customers / read items+promotions but is locked
  out of catalog/settings/promotions/purchases; manager gets the full set. **26/26 assertions
  pass**, proving the model no longer depends on ERPNext role setup. Test users are rolled back /
  torn down — none persisted.
- `bench build` succeeded. Committed as `30cf011`.

**Not done (deliberately):** did NOT strip the ERPNext roles from the live demo users — per the
plan's guardrail, that only happens after this proof + explicit approval, and it's not needed
for the app to be app-owned (the app roles now stand on their own; the extra roles are just
harmless redundancy on the demo users).

**Docs:** no `business.md` / `tests.md` change — this hardens *where* the existing two-tier
contract lives (now shipped in-app) without changing any capability, route, doctype, API, or the
rule itself (verified: zero access-widening). Happy to add a "Permissions" section to either doc
if you want it documented — will ask before writing, per the ownership rule.

## Status
`approved` — implemented, applied live, and proven. See Execution Note.
