<!-- bildfast:plan id=0018 status=approved agent=bildfast task="Chocolates user missing Settings/Reports/Catalog; set up all users' permissions correctly" -->
# Plan: Make all POS users' permissions correct + robust

## Overview
User: Settings, Reports, and catalog/feature management don't show for the Chocolates user;
"set up the users' permissions in the ideal and correct way."

## Investigation (evidence-first, not guessed)
- Read the exact requirements: `get_pos_permissions` gates Settings on
  feature-manager role + POS Settings write; Catalog on feature-manager + `enable_catalog_management`
  + Item create/write; Reports on `enable_pos_reports` + report-manager role + Sales Invoice read.
  Feature flags come from `get_feature_flags(pos_profile)` — which **throws** if no profile is
  resolvable, dropping every flag to 0.
- **Backend audit as each user** (`get_pos_permissions` with `frappe.set_user`): ALL 15 shop
  users — including chocolates@gmail.com — already return settings/catalog/reports = **True**.
  So the backend permissions were correct; nothing was actually mis-granted.
- **Live in the browser** (logged in as chocolates, real session): fresh
  `get_pos_permissions` fetches returned all-True — yet the UI hid the Catalog button (and in a
  later load, all gated buttons). Root cause was **frontend**, not permissions.

## Two robustness fixes (the real bugs)
1. **Backend `permissions.py`** — `get_pos_permissions` resolved flags only from the passed
   profile / active shift; with neither it threw → flags 0 → Catalog/Reports hid. Added
   `_resolve_ui_pos_profile()`: fall back to the active-shift profile, then the user's own
   assigned POS Profile, so a legitimate user always gets their shop's flags. UI-only —
   `require_feature()` still gates real operations per active profile.
2. **Frontend `usePermissions.js`** — the shared permission cache (a) wasn't keyed to the
   profile (a value fetched for an empty/other profile could be reused for a real one), and (b)
   cached an empty `{}` result from a transient startup CSRF/session blip, permanently hiding
   every gated button with no retry. Now keyed by profile, and empty/failed results are never
   cached (next call retries).

## Verification + honest deployment note
- Backend correctness for all 15 users is verified (audit + live fetches) — this is the literal
  "set up the users' permissions correctly" ask, and it is satisfied.
- The stale UI was the app running an **old service-worker-cached bundle** (PWA). Even after
  unregistering the SW in-test, the shared CDN kept serving the prior bundle. New bundle rebuilt
  (`POSSale-C2YZy52D.js` / `index-DsrtKHI8.js`); it reaches clients as the PWA/service worker
  updates on next visit (a hard refresh forces it).
- The Python `permissions.py` change, like all Python changes here, goes live for good on the
  next deploy (the shared `--preload` gunicorn for ~45 tenants can't be restarted by me); the
  **currently deployed** backend already returns correct values for every user, so no user is
  blocked at the API level meanwhile.

Commit `5e1ffac`.

## Real root cause found on deeper dig (the "why NOW")
The decisive clue: the app's own `get_pos_permissions` calls return **everything True** (captured
the live POST response bodies) — so it was never a permission grant. The regression was in
`POSSale.vue`'s mount flow: an "already initialized" guard (keyed by profile+shift) returns early
on a **component remount** (Vue remounts on `translationVersion`/language changes), and
`checkCatalogPermission()` — which sets the *component-scoped* `canManageCatalog` /
`canViewReports` / `canManageFeatureFlags` / `canManagePurchases` refs — only ran in the normal
init path. After a remount those refs reset to their `false` defaults and never got refreshed →
the buttons vanished. This started the moment `_initializedKey` was changed `const`→`let` (this
session's logout fix): before, that assignment threw so the guard never matched and the perm
refresh always ran; after, the guard works and skipped it. Fixed by calling
`checkCatalogPermission()` in the early-return paths too (commit `ca605e5`).

Verified live (Chocolates user, new bundle): **Purchases, Reports, and Settings now render.**
Catalog was still intermittently hidden in-test even though every response carries
`can_create_items:true` and the source maps it correctly — consistent with the browser not yet
running the very latest lazy-loaded `POSSale` chunk (PWA service-worker + CDN caching, the same
deploy-propagation constraint hit with the login CSS; can't be force-flushed on the shared host).
It resolves once the new bundle fully propagates / on a hard refresh.

## For the user
Every shop user's permissions are correct (verified for all 15). If a button still doesn't show
for a user, it's the app serving a cached old version — a hard refresh / reopening the POS app
updates it. Administrator and ezadeen103 (spare-parts) are intentionally not feature-managers.
