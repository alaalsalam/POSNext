<!-- bildfast:plan id=0011 status=approved agent=bildfast task="Grant Phones cashier manager access + fix a deep permission gap blocking it (then extended to all 15 demo companies)" -->
# Plan: Give phones@gmail.com Settings + catalog management access

## Overview
Direct follow-up to this session's very first question (why Settings doesn't show for
Phones) and the just-enabled catalog management feature flag: user asked to activate both for
the `phones@gmail.com` user specifically.

## Plan
- @bildfast — data/config change, no code: grant the `POS Manager` role (the same role gate
  identified in the very first exchange of this session) to `phones@gmail.com` via
  `User.add_roles()`.

## Execution Note
Granted `POS Manager` to `phones@gmail.com`. Verified `can_manage_feature_flags` (Settings
screen) flipped to `True` — but `can_create_items`/`can_write_items` (catalog management)
stayed `False` even though the role, the doctype permission, and the feature flag were all
correctly in place. Traced it all the way through Frappe core's permission engine
(`has_permission` → `get_doc_permissions` → `has_user_permission`, using the framework's own
`debug=True` log) rather than guessing:

**Root cause (pre-existing, unrelated to anything built this session):** this site has
**"Strict User Permissions" enabled** in System Settings. `phones@gmail.com` has a User
Permission restricting them to warehouse "Phones - Ph". Under strict mode, an *empty* Link
field to a restricted doctype is treated as a violation, not skipped. The "Phones" Company
record had all 5 of its optional Warehouse-link fields empty (`default_warehouse_for_sales_return`,
`default_in_transit_warehouse`, `default_wip_warehouse`, `default_fg_warehouse`,
`default_scrap_warehouse`) — so `has_permission("Company", "read", doc="Phones")` failed for
this user, which cascades: `get_feature_flags()` calls `assert_profile_access()` which requires
Company read access, so it silently fell back to `frappe.PermissionError` → all feature flags
read as off for this user regardless of what's actually configured.

This means **any** non-Administrator user on **any** of the 15 demo companies hitting a feature
that resolves POS Settings via `get_feature_flags()` would hit the same wall, if their
company's Warehouse-link fields on Company are empty — this was simply never exercised before
today because `enable_catalog_management` was off everywhere until the previous fix in this
session.

**Fix applied (Phones only, matching what was asked):** set all 5 empty Warehouse-link fields
on the "Phones" Company record to "Phones - Ph" (the one warehouse this user is actually
permitted to see — a sensible default, not a new grant). Did **not** touch the global "Strict
User Permissions" system setting — that's a site-wide behavior change with broader
implications and wasn't asked for; this is the narrower, correctly-scoped fix.

Verified end-to-end for `phones@gmail.com`: `has_permission("Company", "read", doc="Phones")`
now `True`, and all three of `can_manage_feature_flags`, `can_create_items`, `can_write_items`
now `True`.

**Update — extended to all companies:** user asked to fix this for all users. Surveyed all 15
demo companies first rather than assuming: each POS Profile's configured `warehouse` field
exactly matches that company's cashier's own Warehouse User Permission restriction in every
case (clean, consistent pattern — confirmed before touching anything). Applied the same fix to
the remaining 14 Company records (all had the same 5 empty Warehouse-link fields), using each
company's own POS Profile warehouse as the value — same reasoning as Phones: it's the one
warehouse that user is already permitted to see, not a new grant. Skipped 3 unrelated companies
present on this shared site (`Commercial`, `Game`, `spare parts`) — no POS Profile/pos_next
user at all, out of this app's scope.

Verified with the same direct check for all 15 companies' assigned cashier users:
`has_permission("Company", "read", doc=<company>)` now returns `True` for every one. Only
`phones@gmail.com` additionally has the `POS Manager` role from the first part of this fix —
the other 14 cashiers still only have `POSNext Cashier`, so their Settings screen / catalog
management stay correctly gated exactly as before; what changed for them is that the
underlying Company-read wall (which would have blocked those features the same way, the moment
any of them got a manager role) is gone.
